"""
Transport adapters: turn some link into a stream of canonical `Reading`s and
accept `Command`s back. Each is a thin `core.Source` implementation.

Built now : SimulatedSource (no hardware), SerialSource (USB *and*
            Bluetooth-Classic -- both are COM ports on Windows),
            HttpIngestSource (ESP32 over WiFi -- POST readings in, command out
            on the same reply; fed by the /api/ingest route in server.py).
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


# --------------------------------------------------------------------------
# HTTP ingest source -- ESP32 over WiFi (POST readings in, command out on reply)
# --------------------------------------------------------------------------
class HttpIngestSource(Source):
    """WiFi transport for the ESP32 zone nodes.

    Unlike the serial sources, this one does not own a link it reads from -- the
    ESP32 is an HTTP *client* that POSTs to us. The /api/ingest route in
    server.py drives this source:

        route --ingest(payload)--> emits Readings, returns pending cmd string
        Hub   --send_command()---> queues a command for the node's next reply

    That is the firmware's "command rides back on the POST reply" pattern: we
    never open a connection *to* the ESP32, so it works behind NAT and in Wokwi.

    Latching + arming live here (server-side), mirroring SimulatedSource and the
    firmware FSM: water/motion stay in ALARM until a RESET (or DISARM for
    motion), even after the raw value recovers. A watchdog marks a silent node
    DISCONNECTED after HEARTBEAT_TIMEOUT_S instead of showing stale data as live.
    """

    HEARTBEAT_TIMEOUT_S = 6.0   # 3 missed 2s cycles (spec FR-NET-4)

    def __init__(self, codec: Codec | None = None, parent=None):
        super().__init__(codec or JsonCodec(), parent)
        self._armed = True
        self._latched: dict[str, bool] = {}       # sensor.key -> latched-in-alarm
        self._pending: dict[str, list[str]] = {}  # canonical zone -> queued actions
        self._last_seen: dict[str, float] = {}    # canonical zone -> ts
        self._disconnected: set[str] = set()      # zones currently marked offline
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._any_seen = False

    # -- Source interface --------------------------------------------------
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        # Link is "down" until the first node checks in.
        self.connection_changed.emit(False)
        self.notice.emit("HTTP ingest ready -- waiting for ESP32 POSTs on /api/ingest.")
        self._thread = threading.Thread(target=self._watchdog, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.connection_changed.emit(False)

    def send_command(self, cmd: Command) -> None:
        """Called by the Hub when an agent clicks a control. Apply it to the
        server-side FSM immediately, then queue it for delivery on the target
        node's next POST reply."""
        action = cmd.action.upper()
        if action == "DISARM":
            self._armed = False
            self._latched["GALLERY.MOTION"] = False
            self.notice.emit("System DISARMED (alarms suppressed for maintenance).")
            self._queue_all("DISARM")
        elif action == "ARM":
            self._armed = True
            self.notice.emit("System ARMED.")
            self._queue_all("ARM")
        elif action == "RESET":
            key = f"{config.canonical_zone(cmd.zone)}.{cmd.sensor}"
            self._latched[key] = False
            self.notice.emit(f"Latched alarm cleared: {key}.")
            self._queue(config.canonical_zone(cmd.zone), "RESET")
        else:
            self._queue(config.canonical_zone(cmd.zone), action)

    # -- called by the /api/ingest route ----------------------------------
    def ingest(self, payload: dict) -> str:
        """Fan one ESP32 JSON blob out into per-sensor Readings and return the
        command string (AUTO / ARM / DISARM / RESET) for this node's reply."""
        zone = config.canonical_zone(payload.get("zone", ""))
        if not zone:
            return "AUTO"

        now = time.time()
        with self._lock:
            self._last_seen[zone] = now
            was_off = zone in self._disconnected
            self._disconnected.discard(zone)
            if not self._any_seen:
                self._any_seen = True
                self.connection_changed.emit(True)
        if was_off:
            self.notice.emit(f"Zone {zone} reconnected.")

        for field, raw in payload.items():
            sensor = config.FIELD_TO_SENSOR.get(str(field).lower())
            if sensor is None:
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            self._emit_sensor(zone, sensor, value)

        return self._next_command(zone)

    # -- internals ---------------------------------------------------------
    def _emit_sensor(self, zone: str, sensor: str, value: float) -> None:
        sdef = config.sensor_lookup(zone, sensor)
        if sdef is None:
            return
        key = sdef.key

        if sensor == "MOTION":
            triggered = self._armed and value >= 0.5
            if triggered:
                self._latched[key] = True
            latched = self._latched.get(key, False) and self._armed
            out_value = 1.0 if latched else 0.0
            state = config.STATE_ALARM if latched else config.STATE_OK
            self.reading_received.emit(Reading(zone, sensor, out_value, state))
            return

        state = classify(sdef, value)
        if sdef.latched:
            if state == config.STATE_ALARM:
                self._latched[key] = True
            if self._latched.get(key, False):
                state = config.STATE_ALARM
        self.reading_received.emit(Reading(zone, sensor, round(value, 1), state))

    def _queue(self, zone: str, action: str) -> None:
        with self._lock:
            self._pending.setdefault(zone, []).append(action)

    def _queue_all(self, action: str) -> None:
        for z in config.ZONES:
            self._queue(z, action)

    def _next_command(self, zone: str) -> str:
        with self._lock:
            q = self._pending.get(zone)
            if q:
                return q.pop(0)
        return "AUTO"

    def _watchdog(self) -> None:
        """Mark a node DISCONNECTED (and recolour its sensors) when its heartbeat
        stops, so the UI never shows stale data as if it were live."""
        while self._running:
            time.sleep(1.0)
            now = time.time()
            with self._lock:
                stale_zones = [
                    z for z, ts in self._last_seen.items()
                    if now - ts > self.HEARTBEAT_TIMEOUT_S and z not in self._disconnected
                ]
                for z in stale_zones:
                    self._disconnected.add(z)
                all_off = self._any_seen and self._last_seen and all(
                    z in self._disconnected for z in self._last_seen
                )
            for z in stale_zones:
                self.notice.emit(f"Zone {z} heartbeat lost -- marking DISCONNECTED.")
                for sdef in config.SENSORS:
                    if sdef.zone == z:
                        self.reading_received.emit(
                            Reading(z, sdef.sensor, 0.0, config.STATE_DISCONNECTED))
            if all_off:
                self.connection_changed.emit(False)
