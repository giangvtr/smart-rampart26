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

import building
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

    # baselines for the five real-rig sensors; everything else is derived
    REAL_BASELINES = {
        "GALLERY.TEMP": 21.0,
        "GALLERY.HUMIDITY": 50.0,
        "GALLERY.LIGHT": 300.0,
        "GALLERY.MOTION": 0.0,
        "BASEMENT.WATER": 40.0,
    }

    def __init__(self, codec: Codec | None = None, parent=None):
        super().__init__(codec, parent)
        self._thread: threading.Thread | None = None
        self._running = False
        self._armed = True                    # security sub-state (ARMED at night)
        self._latched: dict[str, bool] = {}   # sensor.key -> latched-in-alarm
        # Simulated rooms auto-clear their latches (see _latch). The real rig
        # does NOT: there, a latched alarm holds until an operator RESETs it,
        # which is the behaviour the firmware and the demo script rely on.
        self._latch_until: dict[str, float] = {}
        # smooth baselines per sensor for a natural wander
        self._base = {s.key: self._default_base(s) for s in config.SENSORS}
        self._base.update(self.REAL_BASELINES)
        # the value each sensor drifts back toward once an excursion ends --
        # without it a random walk that reaches 900 adc simply stays there
        self._rest = dict(self._base)
        self._next_sample: dict[str, float] = {}
        # scripted incident state (see building.INCIDENTS)
        self._incident: tuple[str, dict] | None = None
        self._incident_until = 0.0
        self._next_incident = time.time() + random.uniform(*building.INCIDENT_GAP_S)

    @staticmethod
    def _default_base(sdef) -> float:
        """A resting value that classifies as OK.

        Two-sided sensors (temperature, humidity) sit mid-band; one-sided ones
        (water, smoke, sound...) rest low, well under their warn ceiling.
        """
        if sdef.warn and sdef.warn[0] is not None and sdef.warn[1] is not None:
            return (sdef.warn[0] + sdef.warn[1]) / 2.0
        if sdef.kind == "event":
            return 0.0
        return sdef.vmin + 0.15 * (sdef.vmax - sdef.vmin)

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
            self._latch_until.pop(key, None)
            self.notice.emit(f"Latched alarm cleared: {key}.")

    # -- internals ---------------------------------------------------------
    def _loop(self) -> None:
        while self._running:
            now = time.time()
            self._tick_incident(now)
            for sdef in config.SENSORS:
                due = self._next_sample.get(sdef.key, 0.0)
                if now < due:
                    continue
                self._next_sample[sdef.key] = now + sdef.period_s
                value, state = self._sample(sdef, now)
                self.reading_received.emit(Reading(sdef.zone, sdef.sensor, value, state))
            time.sleep(0.05)

    # -- scripted incidents ------------------------------------------------
    def _tick_incident(self, now: float) -> None:
        """Start/stop the periodic correlated incident in a simulated room.

        Left to independent random walks the building is a wall of green with
        the odd unrelated blip. Real alarms corroborate -- a disturbed case
        tilts AND vibrates AND makes noise at the same moment -- so the demo
        drives several sensors in one room together.
        """
        if self._incident is not None:
            if now >= self._incident_until:
                room, _ = self._incident
                self._incident = None
                self._next_incident = now + random.uniform(*building.INCIDENT_GAP_S)
                self.notice.emit(f"[{room}] incident cleared (simulated).")
            return

        if now < self._next_incident:
            return

        room = random.choice(list(building.INCIDENTS))
        label, targets = building.INCIDENTS[room]
        self._incident = (room, targets)
        self._incident_until = now + building.INCIDENT_HOLD_S
        self.notice.emit(f"[{room}] {label} — simulated incident.")

    def _incident_target(self, sdef) -> float | None:
        """The value this sensor is being driven toward, if it is caught up in
        the running incident."""
        if self._incident is None:
            return None
        room, targets = self._incident
        if sdef.room != room:
            return None
        return targets.get(sdef.sensor)

    # -- latching ----------------------------------------------------------
    def _latch(self, sdef, now: float) -> None:
        """Put a latching sensor into ALARM.

        A simulated sensor also books its own release, so 48 demo sensors don't
        each latch once and leave the whole building stuck red; the real rig
        holds until RESET, exactly like the firmware.
        """
        self._latched[sdef.key] = True
        if sdef.synthetic and sdef.key not in self._latch_until:
            self._latch_until[sdef.key] = now + random.uniform(8.0, 18.0)

    def _is_latched(self, sdef, now: float) -> bool:
        if not self._latched.get(sdef.key, False):
            return False
        release = self._latch_until.get(sdef.key)
        if release is not None and now >= release:
            self._latched[sdef.key] = False
            del self._latch_until[sdef.key]
            return False
        return True

    # -- sampling ----------------------------------------------------------
    def _sample(self, sdef, now: float):
        key = sdef.key
        target = self._incident_target(sdef)

        if sdef.kind == "event":
            return self._sample_event(sdef, target, now)

        base = self._base[key]
        if target is not None:
            # ramp toward the incident value rather than snapping, so the chart
            # shows a climb the way a real excursion would
            base += (target - base) * 0.35
        else:
            # pull back toward rest, then wander. Simulated rooms recover briskly
            # (~30 s) so the building doesn't accumulate stuck-red rooms over a
            # long demo; the real rig drifts back slowly, as a real room would.
            base += (self._rest[key] - base) * (0.10 if sdef.synthetic else 0.02)
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
                self._latch(sdef, now)
            if self._is_latched(sdef, now):
                state = config.STATE_ALARM  # stay latched until RESET
        return value, state

    def _sample_event(self, sdef, target, now: float):
        """Discrete sensors: motion, door contacts, case tilt, keypad failures.

        They sit at rest and blip, and (like the firmware) only count while the
        system is ARMED -- DISARM is the "someone's cleaning" switch.

        Simulated ones blip rarely: the interesting trips come from the scripted
        incidents, and 13 event sensors firing independently would just be noise.
        """
        blip_p = 0.002 if sdef.synthetic else 0.03
        if self._armed and (target is not None or random.random() < blip_p):
            self._latch(sdef, now)

        latched = self._is_latched(sdef, now) and self._armed
        if not latched:
            return 0.0, config.STATE_OK

        # a latched event sensor reports its "tripped" magnitude: booleans read
        # 1, graded ones (tilt angle, failed-PIN count) read their alarm level
        if target is not None:
            value = round(target, 1)
        elif sdef.vmax <= 1:
            value = 1.0
        else:
            hi = (sdef.alarm or (None, sdef.vmax))[1] or sdef.vmax
            value = round(min(sdef.vmax, hi + 1), 1)
        return value, config.STATE_ALARM


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
