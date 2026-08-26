"""
Transport-agnostic core: the canonical data model + the Source/Codec interfaces.

This is the ONLY module the UI, storage and control layers import from when they
talk about "incoming data". Nothing here knows whether bytes arrive over USB
serial, Bluetooth or WiFi -- that is the job of the adapters in transports.py.

Boundary shape
--------------
    raw wire bytes  <--Codec-->  Reading / Command  --> the whole app

A `Source` (a transport adapter) owns some link, uses a `Codec` to turn frames
into `Reading`s (emitted via the `reading_received` signal) and to turn a
`Command` into bytes it writes back on `send_command`. Swap the transport = swap
the Source; swap the wire encoding = swap the Codec. Neither touches the UI.
"""
from __future__ import annotations

import json
import time
from abc import abstractmethod
from dataclasses import dataclass, field

import config


# --------------------------------------------------------------------------
# Event -- a minimal, framework-agnostic observer
# --------------------------------------------------------------------------
class Event:
    """A tiny signal/slot primitive with no GUI-framework dependency.

    Deliberately framework-agnostic: the engine must not depend on the
    presentation layer, so a transport can be driven headless (tests, a future
    frontend) as easily as by the web server. Callbacks fire on whichever
    thread called ``emit`` -- the server fans them out to browsers over SSE.
    """

    def __init__(self) -> None:
        self._subscribers: list = []

    def connect(self, fn):
        self._subscribers.append(fn)
        return fn

    def disconnect(self, fn) -> None:
        if fn in self._subscribers:
            self._subscribers.remove(fn)

    def emit(self, *args) -> None:
        # a misbehaving subscriber must never kill a transport read loop
        for fn in list(self._subscribers):
            try:
                fn(*args)
            except Exception:  # pragma: no cover - defensive
                pass


# --------------------------------------------------------------------------
# Canonical model -- the one internal format the app speaks
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Reading:
    """One sensor sample, transport-independent."""
    zone: str
    sensor: str
    value: float
    state: str                 # one of config.STATE_*
    ts: float = field(default_factory=time.time)   # epoch seconds (local clock)

    @property
    def key(self) -> str:
        return f"{self.zone}.{self.sensor}"


@dataclass(frozen=True)
class Command:
    """A control message sent back toward the node."""
    zone: str          # "SYSTEM" for whole-system commands
    sensor: str        # "ALL" when not sensor-specific
    action: str        # e.g. RESET, ARM, DISARM, ACK

    # convenience constructors for the actions the dashboard actually issues
    @staticmethod
    def reset(zone: str, sensor: str) -> "Command":
        return Command(zone, sensor, "RESET")

    @staticmethod
    def arm() -> "Command":
        return Command("SYSTEM", "ALL", "ARM")

    @staticmethod
    def disarm() -> "Command":
        return Command("SYSTEM", "ALL", "DISARM")


# --------------------------------------------------------------------------
# Codec -- how a Reading/Command is encoded on the wire
# --------------------------------------------------------------------------
class Codec:
    """Encode/decode between wire frames and the canonical model.

    `decode_reading` returns a Reading or None (ignore junk / partial lines).
    Adapters call `encode_command` to serialise a Command for transmission.
    """

    def decode_reading(self, frame: str) -> Reading | None:  # pragma: no cover - interface
        raise NotImplementedError

    def encode_command(self, cmd: Command) -> str:           # pragma: no cover - interface
        raise NotImplementedError


class LineCodec(Codec):
    """Reference CSV protocol (spec FR-DASH-1).

    Reading  line : ``ZONE,SENSOR,VALUE,STATE,TIMESTAMP\n``
    Command  line : ``CMD,ZONE,SENSOR,ACTION\n``

    TIMESTAMP on the wire is informational (the node's uptime clock); we stamp
    Readings with the laptop clock on arrival so logging is consistent.
    """

    def decode_reading(self, frame: str) -> Reading | None:
        frame = frame.strip()
        if not frame or frame.startswith("#") or frame.startswith("CMD"):
            return None
        parts = frame.split(",")
        if len(parts) < 4:
            return None
        zone, sensor, raw_value, state = parts[0], parts[1], parts[2], parts[3]
        try:
            value = float(raw_value)
        except ValueError:
            return None
        state = state.strip().upper()
        if state not in config.STATE_COLORS:
            state = config.STATE_OK
        return Reading(zone.strip().upper(), sensor.strip().upper(), value, state)

    def encode_command(self, cmd: Command) -> str:
        return f"CMD,{cmd.zone},{cmd.sensor},{cmd.action}\n"


class JsonCodec(Codec):
    """Alternative JSON protocol -- ready for a WiFi/WebSocket module that would
    rather emit ``{"zone":..,"sensor":..,"value":..,"state":..}`` per frame.

    Provided so switching a transport's encoding is a one-line change; not used
    by the default serial path.
    """

    def decode_reading(self, frame: str) -> Reading | None:
        frame = frame.strip()
        if not frame:
            return None
        try:
            d = json.loads(frame)
        except (ValueError, TypeError):
            return None
        if "cmd" in d or "action" in d:
            return None
        try:
            state = str(d.get("state", config.STATE_OK)).upper()
            if state not in config.STATE_COLORS:
                state = config.STATE_OK
            return Reading(
                str(d["zone"]).upper(),
                str(d["sensor"]).upper(),
                float(d["value"]),
                state,
            )
        except (KeyError, ValueError, TypeError):
            return None

    def encode_command(self, cmd: Command) -> str:
        return json.dumps(
            {"cmd": True, "zone": cmd.zone, "sensor": cmd.sensor, "action": cmd.action}
        ) + "\n"


# --------------------------------------------------------------------------
# Source -- the transport interface every adapter implements
# --------------------------------------------------------------------------
class Source:
    """A data source (transport adapter).

    Events let the app stay ignorant of the transport:
      * ``reading_received(Reading)`` -- a fresh canonical sample arrived.
      * ``connection_changed(bool)`` -- link up/down (drives the DISCONNECTED UI).
      * ``notice(str)`` -- human-readable status/errors for the log pane.

    These are plain `Event`s with no GUI-framework dependency, so the same
    Source works headless as well as under the web server. Subclasses implement
    ``start``, ``stop`` and ``send_command``.
    """

    def __init__(self, codec: Codec | None = None, parent=None):
        # `parent` is accepted and ignored -- kept so adapters can keep the
        # familiar (codec, parent) signature.
        self.codec: Codec = codec or LineCodec()
        self.reading_received = Event()   # -> Reading
        self.connection_changed = Event()  # -> bool
        self.notice = Event()              # -> str

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def send_command(self, cmd: Command) -> None: ...
