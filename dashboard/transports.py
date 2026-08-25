"""
Transport adapters: turn some link into a stream of canonical `Reading`s and
accept `Command`s back. Each is a thin `core.Source` implementation.

Built now : SimulatedSource (no hardware), SerialSource (USB *and*
            Bluetooth-Classic -- both are COM ports on Windows).
Stubbed   : WebSocketSource (WiFi/ESP), BleSource (HM-10 BLE) -- real extension
            points that already satisfy the interface; fill in when needed.

Downstream code only ever sees `core.Reading`/`core.Command`, so adding a
transport never touches the UI, storage or plots.
"""
from __future__ import annotations

import random
import threading
import time

import config
from core import Codec, Command, JsonCodec, LineCodec, Reading, Source


# --------------------------------------------------------------------------
# Shared helper: classify a raw value into OK / WARN / ALARM from thresholds.
# Used by the simulator and as the dashboard's fallback if a frame lacks STATE.
# --------------------------------------------------------------------------
def classify(sensor_def, value: float) -> str:
    def outside(bounds):
        if bounds is None:
            return False
        low, high = bounds
        if low is not None and value < low:
            return True
        if high is not None and value > high:
            return True
        return False

    if outside(sensor_def.alarm):
        return config.STATE_ALARM
    if outside(sensor_def.warn):
        return config.STATE_WARN
    return config.STATE_OK


# --------------------------------------------------------------------------
# Simulated source -- realistic-ish telemetry with occasional excursions
# --------------------------------------------------------------------------
class SimulatedSource(Source):
    """Generates fake but plausible data for every configured sensor and honors
    commands so the disarm/override flow is fully demoable with no Arduino.

    Latching mirrors the firmware FSM: water & motion, once in ALARM, stay in
    ALARM until a RESET command (or, for motion, a DISARM) clears them.
    """

    def __init__(self, codec: Codec | None = None, parent=None):
        super().__init__(codec, parent)
        self._thread: threading.Thread | None = None
        self._running = False
        self._armed = True                    # security sub-state (ARMED at night)
        self._latched: dict[str, bool] = {}   # sensor.key -> latched-in-alarm
        # smooth baselines per sensor for a natural wander
        self._base = {
            "GALLERY.TEMP": 21.0,
            "GALLERY.HUMIDITY": 50.0,
            "GALLERY.LIGHT": 300.0,
            "GALLERY.MOTION": 0.0,
            "BASEMENT.WATER": 40.0,
        }
        self._next_sample: dict[str, float] = {}

    # -- Source interface --------------------------------------------------
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self.connection_changed.emit(True)
        self.notice.emit("Simulated source started (no hardware).")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.connection_changed.emit(False)

    def send_command(self, cmd: Command) -> None:
        # exactly the path the real node would react to -- but in-process.
        if cmd.action == "DISARM":
            self._armed = False
            self._latched["GALLERY.MOTION"] = False
            self.notice.emit("System DISARMED (alarms suppressed for maintenance).")
        elif cmd.action == "ARM":
            self._armed = True
            self.notice.emit("System ARMED.")
        elif cmd.action == "RESET":
            key = f"{cmd.zone}.{cmd.sensor}"
            self._latched[key] = False
            self.notice.emit(f"Latched alarm cleared: {key}.")

    # -- internals ---------------------------------------------------------
    def _loop(self) -> None:
        while self._running:
            now = time.time()
            for sdef in config.SENSORS:
                due = self._next_sample.get(sdef.key, 0.0)
                if now < due:
                    continue
                self._next_sample[sdef.key] = now + sdef.period_s
                value, state = self._sample(sdef, now)
                self.reading_received.emit(Reading(sdef.zone, sdef.sensor, value, state))
            time.sleep(0.05)

    def _sample(self, sdef, now: float):
        key = sdef.key
        base = self._base[key]

        if key == "GALLERY.MOTION":
            # random blips; only meaningful while ARMED
            triggered = self._armed and random.random() < 0.03
            if triggered:
                self._latched[key] = True
            latched = self._latched.get(key, False)
            value = 1.0 if (latched and self._armed) else 0.0
            state = config.STATE_ALARM if (latched and self._armed) else config.STATE_OK
            return value, state

        # environmental / water: wander around baseline, occasional excursion
        base += random.uniform(-0.4, 0.4)
        # rare push toward a danger zone so the demo shows colour changes
        if random.random() < 0.01:
            base += random.choice([-1, 1]) * (sdef.vmax - sdef.vmin) * 0.15
        base = max(sdef.vmin, min(sdef.vmax, base))
        self._base[key] = base
        value = round(base, 1)

        state = classify(sdef, value)
        if sdef.latched:
            if state == config.STATE_ALARM:
                self._latched[key] = True
            if self._latched.get(key, False):
                state = config.STATE_ALARM  # stay latched until RESET
        return value, state


# --------------------------------------------------------------------------
# Serial source -- USB serial AND Bluetooth-Classic (both are COM ports)
# --------------------------------------------------------------------------
class SerialSource(Source):
    """Reads newline-delimited frames from a serial/COM port via pyserial.

    On Windows an HC-05/06 Bluetooth-Classic module pairs as an outgoing COM
    port, so this same class handles USB *and* classic Bluetooth with no change
    -- only the port name differs. Guarded import keeps the app runnable without
    pyserial installed (falls back to a clear notice on start()).
    """

    def __init__(self, port: str = config.SERIAL_PORT, baud: int = config.SERIAL_BAUD,
                 codec: Codec | None = None, parent=None):
        super().__init__(codec, parent)
        self.port = port
        self.baud = baud
        self._serial = None
        self._serial_mod = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        try:
            import serial  # pyserial
        except ImportError:
            self.notice.emit("pyserial not installed -- run: pip install pyserial")
            self.connection_changed.emit(False)
            return
        self._serial_mod = serial
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self.connection_changed.emit(False)

    def send_command(self, cmd: Command) -> None:
        frame = self.codec.encode_command(cmd)
        try:
            if self._serial and self._serial.is_open:
                self._serial.write(frame.encode("utf-8"))
                self.notice.emit(f"Sent: {frame.strip()}")
            else:
                self.notice.emit("Cannot send command: serial not connected.")
        except Exception as exc:  # pragma: no cover - hardware dependent
            self.notice.emit(f"Serial write failed: {exc}")

    def _loop(self) -> None:
        # (Re)connect + read loop with resilience: a dropped link reports
        # DISCONNECTED (FR-DASH-7) and keeps retrying rather than crashing.
        while self._running:
            if self._serial is None or not self._serial.is_open:
                try:
                    self._serial = self._serial_mod.Serial(self.port, self.baud, timeout=1.0)
                    self.connection_changed.emit(True)
                    self.notice.emit(f"Serial connected on {self.port} @ {self.baud}.")
                except Exception as exc:
                    self.connection_changed.emit(False)
                    self.notice.emit(f"Serial connect failed ({exc}); retrying...")
                    time.sleep(2.0)
                    continue
            try:
                raw = self._serial.readline()
                if not raw:
                    continue
                frame = raw.decode("utf-8", errors="replace")
                reading = self.codec.decode_reading(frame)
                if reading is not None:
                    self.reading_received.emit(reading)
            except Exception as exc:
                self.notice.emit(f"Serial read error ({exc}); reconnecting...")
                self.connection_changed.emit(False)
                try:
                    self._serial.close()
                except Exception:
                    pass
                self._serial = None
                time.sleep(1.0)


# --------------------------------------------------------------------------
# Stubs -- real extension points for later transports
# --------------------------------------------------------------------------
class WebSocketSource(Source):
    """WiFi/ESP path. An ESP8266/ESP32 pushing frames over a WebSocket would use
    this. Default codec would typically be JsonCodec. TODO: implement with the
    `websockets` package (guarded import), running its asyncio loop in a thread
    and emitting `reading_received` per message. Interface is already correct."""

    def __init__(self, url: str = "ws://192.168.4.1:81", codec: Codec | None = None, parent=None):
        super().__init__(codec or JsonCodec(), parent)
        self.url = url

    def start(self) -> None:
        self.notice.emit("WebSocketSource is a stub -- WiFi transport not implemented yet.")
        self.connection_changed.emit(False)

    def stop(self) -> None:
        pass

    def send_command(self, cmd: Command) -> None:
        self.notice.emit("WebSocketSource stub: command ignored.")


class BleSource(Source):
    """Bluetooth Low Energy (HM-10) path. TODO: implement with `bleak`
    (guarded import), subscribing to the module's notify characteristic and
    writing commands to its write characteristic. Interface already matches."""

    def __init__(self, address: str = "", codec: Codec | None = None, parent=None):
        super().__init__(codec or LineCodec(), parent)
        self.address = address

    def start(self) -> None:
        self.notice.emit("BleSource is a stub -- BLE transport not implemented yet.")
        self.connection_changed.emit(False)

    def stop(self) -> None:
        pass

    def send_command(self, cmd: Command) -> None:
        self.notice.emit("BleSource stub: command ignored.")
