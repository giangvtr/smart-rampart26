"""
MuseumGuard dashboard — entry point.

Builds the main window (a pyqtgraph DockArea of movable/resizable/floatable
panels), picks a data Source, and wires everything together:

    Source.reading_received --> Storage + SensorPanels + StatusPanel + AlarmBanner
    ControlPanel commands    --> (login-gated) Source.send_command + audit log

Run:  python -m dashboard.app            (from the repo root)
  or: python app.py                      (from the dashboard/ folder)

Switch transport by changing make_source() below — nothing else changes.
"""
from __future__ import annotations

import sys
import time

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QMessageBox, QPlainTextEdit, QStatusBar,
    QVBoxLayout, QWidget,
)
from pyqtgraph.dockarea import Dock, DockArea

import anomaly
import config
from panels import AlarmBanner, ControlPanel, LoginDialog, SensorPanel, StatusPanel
from security import Session
from storage import Storage
from transports import SerialSource, SimulatedSource  # noqa: F401 (SerialSource for the swap)


def make_source():
    """The single swap-point for how data reaches the dashboard.

    Default: SimulatedSource (no hardware). For the real Arduino over USB or
    Bluetooth-Classic, comment the first line and use the second (set the port
    in config.py). WiFi/BLE stubs live in transports.py.
    """
    return SimulatedSource()
    # return SerialSource(port=config.SERIAL_PORT, baud=config.SERIAL_BAUD)


class _SourceBridge(QObject):
    """Marshals plain-callback Source events onto the Qt GUI thread.

    `core.Source` is deliberately framework-agnostic (plain `Event` callbacks)
    so the web server can reuse it. Those callbacks fire on the transport
    thread, which must never touch widgets directly -- so we re-emit them as Qt
    signals. Emitting a signal from a worker thread is safe; Qt queues delivery
    to the GUI thread where the slots run.
    """

    reading = Signal(object)
    connection = Signal(bool)
    message = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_TITLE)
        self.resize(1280, 820)

        self.storage = Storage()
        self.session = Session()
        self.source = make_source()
        # same engine the web dashboard uses -- see anomaly.py
        self.detector = anomaly.AnomalyEngine()
        self._connected = False
        self._last_seen: dict[str, float] = {}

        # ---- central layout: alarm banner on top, dock area below ----
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(6, 6, 6, 6)
        self.banner = AlarmBanner()
        vbox.addWidget(self.banner)
        self.dock_area = DockArea()
        vbox.addWidget(self.dock_area, 1)
        self.setCentralWidget(central)

        # ---- docks ----
        self.sensor_panels: dict[str, SensorPanel] = {}
        self.docks: dict[str, Dock] = {}
        self._build_sensor_docks()

        self.status_panel = StatusPanel()
        status_dock = Dock("Status", size=(240, 300))
        status_dock.addWidget(self.status_panel)
        self.dock_area.addDock(status_dock, "right")
        self.docks["__status__"] = status_dock

        self.control_panel = ControlPanel()
        control_dock = Dock("Controls", size=(240, 300))
        control_dock.addWidget(self.control_panel)
        self.dock_area.addDock(control_dock, "bottom", status_dock)
        self.docks["__controls__"] = control_dock

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        log_dock = Dock("Event log", size=(240, 200))
        log_dock.addWidget(self.log_view)
        self.dock_area.addDock(log_dock, "bottom", control_dock)
        self.docks["__log__"] = log_dock

        self._build_menu()

        # ---- status bar ----
        self.setStatusBar(QStatusBar())
        self.conn_label = QLabel()
        self.statusBar().addPermanentWidget(self.conn_label)
        self._set_connected(False)

        # ---- wiring ----
        self.control_panel.login_requested.connect(self._do_login)
        self.control_panel.logout_requested.connect(self._do_logout)
        self.control_panel.command_requested.connect(self._on_command)
        # transport-thread callbacks -> Qt signals -> GUI thread slots
        self._bridge = _SourceBridge()
        self._bridge.reading.connect(self._on_reading)
        self._bridge.connection.connect(self._set_connected)
        self._bridge.message.connect(self._log)
        self.source.reading_received.connect(self._bridge.reading.emit)
        self.source.connection_changed.connect(self._bridge.connection.emit)
        self.source.notice.connect(self._bridge.message.emit)

        # ---- timers: repaint plots + stale/disconnect watchdog ----
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(config.UI_REFRESH_MS)
        self._ui_timer.timeout.connect(self._refresh_ui)
        self._ui_timer.start()

        self.source.start()
        self._log(f"{config.APP_NAME} started.")

    # -- construction helpers ---------------------------------------------
    def _build_sensor_docks(self) -> None:
        prev = None
        for sdef in config.SENSORS:
            panel = SensorPanel(sdef, self.storage.buffers[sdef.key])
            dock = Dock(f"{sdef.zone} · {sdef.label}", size=(500, 220), closable=True)
            dock.addWidget(panel)
            if prev is None:
                self.dock_area.addDock(dock, "left")
            else:
                self.dock_area.addDock(dock, "bottom", prev)
            prev = dock
            self.sensor_panels[sdef.key] = panel
            self.docks[sdef.key] = dock

    def _build_menu(self) -> None:
        view_menu = self.menuBar().addMenu("&View")
        # one toggle action per closable dock -> re-add closed panels
        for sdef in config.SENSORS:
            act = QAction(f"{sdef.zone} · {sdef.label}", self, checkable=True, checked=True)
            dock = self.docks[sdef.key]
            act.toggled.connect(lambda on, d=dock: self._toggle_dock(d, on))
            # keep the menu checkbox in sync if the user clicks the dock's X
            dock.sigClosed.connect(lambda a=act: a.setChecked(False))
            view_menu.addAction(act)

    def _toggle_dock(self, dock: Dock, visible: bool) -> None:
        if visible:
            if dock.container() is None:      # was closed -> re-add it
                self.dock_area.addDock(dock, "left")
            dock.show()
        else:
            dock.close()

    # -- data flow --------------------------------------------------------
    def _on_reading(self, reading) -> None:
        self._last_seen[reading.key] = time.time()
        prev_state = self.storage.record_reading(reading)
        self.status_panel.update_sensor(reading.key, reading.value, reading.state)

        for record in self.detector.feed(reading):
            panel = self.sensor_panels.get(record["key"])
            if panel is not None:
                # hand over every window for this sensor, not just the changed
                # one -- the panel redraws its whole overlay each refresh
                panel.set_anomalies([a for a in self.detector.recent(60)
                                     if a["key"] == record["key"]])
            if not record["open"]:
                self._log(f"ANOMALY [{record['zone']}·{record['label']}] "
                          f"{record['kindLabel']} ({record['severity']}) — "
                          f"{record['message']}")

        if prev_state is not None:
            self._log(
                f"[{reading.zone}·{reading.sensor}] {prev_state} -> {reading.state}"
                f" ({reading.value:g} {config.SENSORS_BY_KEY[reading.key].unit})"
            )

    def _refresh_ui(self) -> None:
        alarm_zones = []
        for key, panel in self.sensor_panels.items():
            panel.refresh()
            if panel.buffer.last_state == config.STATE_ALARM:
                alarm_zones.append(config.SENSORS_BY_KEY[key].zone)
        self.banner.set_active(bool(alarm_zones), alarm_zones)

    def _on_command(self, cmd) -> None:
        if not self.session.authenticated:
            QMessageBox.warning(self, "Login required", "Log in before sending overrides.")
            return
        self.source.send_command(cmd)
        actor = self.session.user or "unknown"
        self.storage.record_audit(actor, cmd.action, f"{cmd.zone}.{cmd.sensor}")
        self._log(f"AUDIT: {actor} issued {cmd.action} {cmd.zone}.{cmd.sensor}")

    # -- auth -------------------------------------------------------------
    def _do_login(self) -> None:
        dlg = LoginDialog(self)
        if dlg.exec():
            user, pw = dlg.credentials()
            if self.session.login(user, pw):
                self.control_panel.set_authenticated(True, self.session.user)
                self.storage.record_audit(self.session.user, "LOGIN", "")
                self._log(f"Agent '{self.session.user}' logged in.")
            else:
                QMessageBox.critical(self, "Login failed", "Invalid username or password.")

    def _do_logout(self) -> None:
        if self.session.authenticated:
            self.storage.record_audit(self.session.user, "LOGOUT", "")
            self._log(f"Agent '{self.session.user}' logged out.")
        self.session.logout()
        self.control_panel.set_authenticated(False)

    # -- connection state -------------------------------------------------
    def _set_connected(self, connected: bool) -> None:
        self._connected = connected
        if connected:
            self.conn_label.setText("● CONNECTED")
            self.conn_label.setStyleSheet("color: #2e7d32; font-weight: 600;")
        else:
            self.conn_label.setText("● DISCONNECTED")
            self.conn_label.setStyleSheet("color: #c62828; font-weight: 600;")
            # reflect the loss of link on every status tile (FR-DASH-7)
            for sdef in config.SENSORS:
                last = self.storage.buffers[sdef.key].last_value
                self.status_panel.update_sensor(
                    sdef.key, last if last is not None else 0, config.STATE_DISCONNECTED
                )

    def _log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{ts}] {msg}")

    # -- shutdown ---------------------------------------------------------
    def closeEvent(self, event):
        try:
            self.source.stop()
        finally:
            self.storage.close()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
