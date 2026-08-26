"""
pyqtgraph / PySide6 widgets for the dashboard.

  * SensorPanel  -- one live plot per sensor, threshold bands, state-coloured
                    border/title, per-panel time-scale selector.
  * StatusPanel  -- compact grid of colour-coded zone/sensor tiles.
  * AlarmBanner  -- flashes while any sensor is in ALARM.
  * ControlPanel -- Arm/Disarm + per-sensor Acknowledge, login-gated.
  * LoginDialog  -- basic username/password gate.
"""
from __future__ import annotations

import time

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

import config
from core import Command
from storage import RingBuffer

pg.setConfigOptions(antialias=True, background=None, foreground="d")


def _qcolor(state: str) -> QColor:
    return QColor(config.STATE_COLORS.get(state, "#888888"))


# anomaly severities, warmest = worst (kept in step with the web UI's palette)
_SEVERITY_COLORS = {"LOW": "#d29922", "MEDIUM": "#db6d28", "HIGH": "#f85149"}


# --------------------------------------------------------------------------
# One live sensor plot
# --------------------------------------------------------------------------
class SensorPanel(QWidget):
    """Live plot for a single sensor, fed from a RingBuffer."""

    def __init__(self, sensor_def, buffer: RingBuffer, parent=None):
        super().__init__(parent)
        self.sdef = sensor_def
        self.buffer = buffer
        self._state = config.STATE_DISCONNECTED

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(3)

        # header: value read-out + time-scale selector
        header = QHBoxLayout()
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("font-size: 15px; font-weight: 600;")
        header.addWidget(self.value_label)
        header.addStretch(1)
        self.scale_combo = QComboBox()
        for label, _ in config.TIME_SCALES:
            self.scale_combo.addItem(label)
        self.scale_combo.setCurrentIndex(config.DEFAULT_TIME_SCALE_INDEX)
        header.addWidget(QLabel("window:"))
        header.addWidget(self.scale_combo)
        root.addLayout(header)

        # plot
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setYRange(sensor_def.vmin, sensor_def.vmax)
        self.plot.setLabel("left", sensor_def.unit)
        self.plot.setMouseEnabled(x=True, y=False)
        self.curve = self.plot.plot([], [], pen=pg.mkPen(_qcolor(config.STATE_OK), width=2))
        self._add_threshold_bands()
        root.addWidget(self.plot)

        # Anomaly windows shaded behind the trace. The x-axis is seconds-ago,
        # so every region has to be re-placed on each refresh -- they are held
        # in a reused pool rather than rebuilt, which would thrash the scene.
        self._anomalies: list[dict] = []
        self._anom_items: list[pg.LinearRegionItem] = []

        self.setMinimumHeight(140)
        self._apply_state_style(config.STATE_DISCONNECTED)

    def _add_threshold_bands(self) -> None:
        """Shade warn/alarm regions so the danger zones are visible at a glance."""
        sd = self.sdef

        def band(low, high, color):
            if low is None:
                low = sd.vmin
            if high is None:
                high = sd.vmax
            region = pg.LinearRegionItem(
                values=(low, high), orientation="horizontal",
                brush=pg.mkBrush(color), movable=False,
            )
            region.setZValue(-10)
            self.plot.addItem(region)

        warn_c = QColor(config.STATE_COLORS[config.STATE_WARN]); warn_c.setAlpha(35)
        alarm_c = QColor(config.STATE_COLORS[config.STATE_ALARM]); alarm_c.setAlpha(40)
        # alarm bands (outside the alarm bounds)
        if sd.alarm:
            low, high = sd.alarm
            if low is not None:
                band(sd.vmin, low, alarm_c)
            if high is not None:
                band(high, sd.vmax, alarm_c)
        # warn bands (between warn and alarm bounds)
        if sd.warn:
            wlow, whigh = sd.warn
            alow = sd.alarm[0] if sd.alarm else None
            ahigh = sd.alarm[1] if sd.alarm else None
            if wlow is not None:
                band(alow, wlow, warn_c)
            if whigh is not None:
                band(whigh, ahigh, warn_c)

    def set_anomalies(self, records: list) -> None:
        """Replace the anomaly windows shaded on this plot (see anomaly.py)."""
        self._anomalies = records

    def _refresh_anomalies(self, now: float, oldest: float) -> None:
        """Re-place the shaded regions for the anomalies still on screen."""
        visible = [a for a in self._anomalies if a["t1"] - now >= oldest]
        while len(self._anom_items) < len(visible):
            item = pg.LinearRegionItem(values=(0, 0), movable=False)
            item.setZValue(-9)              # over the threshold bands, under the trace
            self.plot.addItem(item)
            self._anom_items.append(item)

        for item, a in zip(self._anom_items, visible):
            color = QColor(_SEVERITY_COLORS.get(a["severity"], "#d29922"))
            color.setAlpha(55)
            item.setBrush(pg.mkBrush(color))
            item.setRegion((a["t0"] - now, a["t1"] - now))
            item.show()
        for item in self._anom_items[len(visible):]:
            item.hide()

    def _selected_window_s(self):
        return config.TIME_SCALES[self.scale_combo.currentIndex()][1]

    def refresh(self) -> None:
        times, values = self.buffer.arrays()
        if not times:
            return
        now = time.time()
        rel = [t - now for t in times]   # x-axis in seconds-ago (0 = now)
        self.curve.setData(rel, values)

        window = self._selected_window_s()
        if window is None:
            self.plot.setXRange(rel[0], 0, padding=0.02)
        else:
            self.plot.setXRange(-window, 0, padding=0.02)
        self._refresh_anomalies(now, rel[0] if window is None else -window)

        state = self.buffer.last_state or config.STATE_OK
        last = self.buffer.last_value
        if last is not None:
            self.value_label.setText(f"{last:g} {self.sdef.unit}")
        if state != self._state:
            self._apply_state_style(state)

    def _apply_state_style(self, state: str) -> None:
        self._state = state
        color = config.STATE_COLORS.get(state, "#888888")
        self.setStyleSheet(
            f"SensorPanel {{ border: 2px solid {color}; border-radius: 6px; }}"
        )
        self.curve.setPen(pg.mkPen(_qcolor(state), width=2))
        self.value_label.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {color};"
        )


# --------------------------------------------------------------------------
# Status grid
# --------------------------------------------------------------------------
class StatusPanel(QWidget):
    """Grid of colour-coded tiles, one per sensor, worst-state at a glance."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.tiles: dict[str, QLabel] = {}
        for row, sdef in enumerate(config.LIVE_SENSORS):
            name = QLabel(f"{sdef.zone} · {sdef.label}")
            tile = QLabel("--")
            tile.setAlignment(Qt.AlignCenter)
            tile.setMinimumWidth(120)
            self._style_tile(tile, config.STATE_DISCONNECTED)
            layout.addWidget(name, row, 0)
            layout.addWidget(tile, row, 1)
            self.tiles[sdef.key] = tile
        layout.setColumnStretch(0, 1)

    def _style_tile(self, tile: QLabel, state: str) -> None:
        color = config.STATE_COLORS.get(state, "#888888")
        tile.setStyleSheet(
            f"background: {color}; color: white; font-weight: 600;"
            f"padding: 4px 8px; border-radius: 4px;"
        )

    def update_sensor(self, key: str, value: float, state: str) -> None:
        tile = self.tiles.get(key)
        if tile is None:
            return
        tile.setText(f"{value:g}  ·  {state}")
        self._style_tile(tile, state)


# --------------------------------------------------------------------------
# Alarm banner
# --------------------------------------------------------------------------
class AlarmBanner(QLabel):
    """Flashes red while any sensor is in ALARM; hidden otherwise."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(34)
        self._active = False
        self._on = False
        self._timer = QTimer(self)
        self._timer.setInterval(config.BANNER_FLASH_MS)
        self._timer.timeout.connect(self._flash)
        self.set_active(False, [])

    def set_active(self, active: bool, zones: list[str]) -> None:
        self._active = active
        if active:
            self.setText("  ⚠  ACTIVE ALARM: " + ", ".join(sorted(set(zones))) + "  ")
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
            self.setText("  All clear  ")
            self.setStyleSheet(
                "background: #2e7d32; color: white; font-weight: 700; border-radius: 4px;"
            )

    def _flash(self) -> None:
        self._on = not self._on
        bg = config.STATE_COLORS[config.STATE_ALARM] if self._on else "#7f1010"
        self.setStyleSheet(
            f"background: {bg}; color: white; font-weight: 700; border-radius: 4px;"
        )


# --------------------------------------------------------------------------
# Control panel (login-gated)
# --------------------------------------------------------------------------
class ControlPanel(QWidget):
    """Arm/Disarm + per-sensor Acknowledge. Emits a Command to be sent back.

    Everything except the Login button is disabled until an agent logs in
    (FR-DASH-4): read-only monitoring stays open, only overrides are gated.
    """

    command_requested = Signal(object)   # Command
    login_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)

        # login row
        login_row = QHBoxLayout()
        self.login_status = QLabel("Not logged in — overrides locked")
        self.login_status.setStyleSheet("color: #b71c1c; font-weight: 600;")
        self.login_btn = QPushButton("Log in…")
        self.login_btn.clicked.connect(self.login_requested)
        login_row.addWidget(self.login_status, 1)
        login_row.addWidget(self.login_btn)
        root.addLayout(login_row)

        line = QFrame(); line.setFrameShape(QFrame.HLine); root.addWidget(line)

        # arm / disarm
        arm_row = QHBoxLayout()
        self.arm_btn = QPushButton("ARM")
        self.disarm_btn = QPushButton("DISARM (maintenance)")
        self.arm_btn.clicked.connect(lambda: self.command_requested.emit(Command.arm()))
        self.disarm_btn.clicked.connect(lambda: self.command_requested.emit(Command.disarm()))
        arm_row.addWidget(self.arm_btn)
        arm_row.addWidget(self.disarm_btn)
        root.addLayout(arm_row)

        root.addWidget(QLabel("Acknowledge / clear latched alarm:"))
        # per-latching-sensor reset buttons
        self._ack_buttons: list[QPushButton] = []
        for sdef in config.LIVE_SENSORS:
            if not sdef.latched:
                continue
            btn = QPushButton(f"Reset {sdef.zone} · {sdef.label}")
            btn.clicked.connect(
                lambda _=False, s=sdef: self.command_requested.emit(Command.reset(s.zone, s.sensor))
            )
            root.addWidget(btn)
            self._ack_buttons.append(btn)

        root.addStretch(1)
        self.set_authenticated(False)

    def set_authenticated(self, authed: bool, user: str | None = None) -> None:
        for w in [self.arm_btn, self.disarm_btn, *self._ack_buttons]:
            w.setEnabled(authed)
        if authed:
            self.login_status.setText(f"Logged in as {user} — overrides enabled")
            self.login_status.setStyleSheet("color: #1b5e20; font-weight: 600;")
            self.login_btn.setText("Log out")
            try:
                self.login_btn.clicked.disconnect()
            except RuntimeError:
                pass
            self.login_btn.clicked.connect(self.logout_requested)
        else:
            self.login_status.setText("Not logged in — overrides locked")
            self.login_status.setStyleSheet("color: #b71c1c; font-weight: 600;")
            self.login_btn.setText("Log in…")
            try:
                self.login_btn.clicked.disconnect()
            except RuntimeError:
                pass
            self.login_btn.clicked.connect(self.login_requested)


# --------------------------------------------------------------------------
# Login dialog
# --------------------------------------------------------------------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agent login")
        form = QFormLayout(self)
        self.user = QLineEdit("guard")
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        form.addRow("Username", self.user)
        form.addRow("Password", self.pw)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def credentials(self):
        return self.user.text(), self.pw.text()
