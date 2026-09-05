"""
Predictive HVAC controller.

Turns the live temp/RH stream (plus a weather-forecast outlook) into a single
conditioning EFFORT, 0..max_level, and a MODE (IDLE / HEAT / COOL / DEHUMIDIFY /
HUMIDIFY). The effort is delivered to the ESP32 as an LED PWM duty that rides
back on the /api/ingest reply (see server.py + esp32_node.ino).

Three behaviours lift this above a reactive thermostat:

  * Feedforward -- the forecast outlook (forecast.py) nudges effort *before*
    indoor conditions move: pre-emptive dehumidify ahead of a humid front.
  * Passive buffering -- when the outdoor trend will pull conditions back the
    right way on its own, effort is reduced rather than fighting it.
  * Gradual ramping -- the *output* never steps. A background thread eases the
    current effort toward the desired one by at most `max_step_per_s`, so the
    room microclimate changes smoothly (EN 15757 short-term bandwidth), which
    matters for canvas and wood.

Setpoints reuse the TEMP/HUMIDITY *warn* bands from config.SENSORS -- no second
source of truth. Fed the same Readings as the preservation engine, from
Hub._on_reading. Transport-agnostic: under sim/serial the decision still drives
the dashboard, it just is not carried to a physical LED.
"""
from __future__ import annotations

import threading
import time

import config

_OVERRIDES = {"AUTO", "OFF", "HEAT", "COOL", "DEHUMIDIFY", "HUMIDIFY"}


def _warn_band(sensor: str) -> tuple[float, float]:
    """(low, high) comfort band for a sensor token, from config.SENSORS."""
    for s in config.SENSORS:
        if s.sensor == sensor:
            low, high = s.warn
            return (low, high)
    raise KeyError(sensor)


class HvacController:
    """Owns the HVAC decision + the ramp loop. One effort/mode per zone; the demo
    has a single BASEMENT zone but the structure stays per-zone."""

    def __init__(self, forecast, on_state=None, on_forecast=None) -> None:
        self._forecast = forecast
        self._on_state = on_state          # callback(state_dict) -> broadcast SSE
        self._on_forecast = on_forecast    # callback(outlook_dict) -> broadcast SSE
        self._last_forecast_key: tuple | None = None
        cfg = config.HVAC
        self._max = float(cfg["max_level"])
        self._step = float(cfg["max_step_per_s"])
        self._tick = float(cfg["tick_s"])
        self._temp: float | None = None
        self._rh: float | None = None
        self._override = "AUTO"            # AUTO or a forced mode
        self._current = 0.0               # eased effort actually being output
        self._desired = 0.0
        self._mode = "IDLE"
        self._reason = "Starting up"
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_emit_key: tuple | None = None

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        if self._running or not config.HVAC["enabled"]:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    # -- inputs ------------------------------------------------------------
    def feed(self, reading) -> None:
        """Track the latest temp/RH. Ignores stale/disconnected samples."""
        if reading.state in (config.STATE_DISCONNECTED, config.STATE_STALE):
            return
        s = reading.sensor.upper()
        with self._lock:
            if s == "TEMP":
                self._temp = float(reading.value)
            elif s == "HUMIDITY":
                self._rh = float(reading.value)

    def set_override(self, action: str) -> bool:
        """Apply a guard override. Returns True if it was a recognised action."""
        action = action.upper()
        if action not in _OVERRIDES:
            return False
        with self._lock:
            self._override = action
        return True

    # -- outputs -----------------------------------------------------------
    def level_for(self, zone: str) -> int:
        """Current eased effort (0..max_level) for a zone's reply."""
        with self._lock:
            return int(round(self._current))

    def state(self) -> dict:
        with self._lock:
            return self._state_locked()

    def _state_locked(self) -> dict:
        pct = 0 if self._max == 0 else round(100 * self._current / self._max)
        return {
            "mode": self._mode,
            "level": int(round(self._current)),
            "target": int(round(self._desired)),
            "maxLevel": int(self._max),
            "percent": pct,
            "override": self._override,
            "reason": self._reason,
        }

    # -- control law -------------------------------------------------------
    def _compute(self, fo: dict) -> tuple[str, float, str]:
        """Return (mode, desired_effort, reason) from readings + forecast + override."""
        cfg = config.HVAC
        if self._override == "OFF":
            return "IDLE", 0.0, "Manual override: HVAC off"
        if self._override in ("HEAT", "COOL", "DEHUMIDIFY", "HUMIDIFY"):
            return self._override, self._max, f"Manual override: {self._override.lower()}"

        if self._temp is None or self._rh is None:
            return "IDLE", 0.0, "Waiting for temp/humidity readings"

        t_lo, t_hi = _warn_band("TEMP")
        h_lo, h_hi = _warn_band("HUMIDITY")

        # reactive demand for each mode, 0..1 of full scale
        demands: dict[str, float] = {}
        if self._temp < t_lo:
            demands["HEAT"] = (t_lo - self._temp) / cfg["temp_full_scale"]
        elif self._temp > t_hi:
            demands["COOL"] = (self._temp - t_hi) / cfg["temp_full_scale"]
        if self._rh > h_hi:
            demands["DEHUMIDIFY"] = (self._rh - h_hi) / cfg["rh_full_scale"]
        elif self._rh < h_lo:
            demands["HUMIDIFY"] = (h_lo - self._rh) / cfg["rh_full_scale"]

        # feedforward + passive buffering: the forecast nudges the relevant demand.
        # A humid/warm front pushes dehumidify/cool up pre-emptively; an incoming
        # cool/dry spell lets us coast (negative nudge = passive buffering).
        w = cfg["forecast_weight"]
        fs = cfg["forecast_full_scale"]
        pre = ""
        if fo["d_rh"] != 0:
            demands["DEHUMIDIFY"] = demands.get("DEHUMIDIFY", 0.0) + w * (fo["d_rh"] / fs)
        if fo["d_temp_c"] > 0:
            demands["COOL"] = demands.get("COOL", 0.0) + w * (fo["d_temp_c"] / fs)
        elif fo["d_temp_c"] < 0:
            demands["HEAT"] = demands.get("HEAT", 0.0) + w * (-fo["d_temp_c"] / fs)

        # pick the strongest demand
        demands = {m: d for m, d in demands.items() if d > 0.02}
        if not demands:
            reason = "Within comfort band"
            if fo["trend"] != "steady":
                reason += f" — {fo['label'].lower()}, holding"
            return "IDLE", 0.0, reason

        mode = max(demands, key=demands.get)
        effort = max(0.0, min(1.0, demands[mode])) * self._max

        reactive_hit = (
            (mode == "HEAT" and self._temp < t_lo) or
            (mode == "COOL" and self._temp > t_hi) or
            (mode == "DEHUMIDIFY" and self._rh > h_hi) or
            (mode == "HUMIDIFY" and self._rh < h_lo)
        )
        verb = mode.capitalize()
        if reactive_hit:
            detail = (f"RH {self._rh:.0f}% vs {h_hi:.0f}% band" if mode == "DEHUMIDIFY"
                      else f"RH {self._rh:.0f}% vs {h_lo:.0f}% band" if mode == "HUMIDIFY"
                      else f"temp {self._temp:.0f}°C vs {t_lo:.0f}–{t_hi:.0f}°C band")
            reason = f"{verb} — {detail}"
        else:
            pre = "Pre-emptive "
            reason = f"{pre}{verb.lower()} — {fo['label'].lower()} in {fo['horizon_h']:.0f} h"
        return mode, effort, reason

    def _loop(self) -> None:
        while self._running:
            # fetch the outlook once per tick (outside the lock -- an http forecast
            # returns a cached value, but keep the network read off the lock) and
            # broadcast it as its own persistent state when it meaningfully changes.
            fo = self._forecast.outlook()
            fkey = (fo["trend"], round(fo["out_temp_c"]), round(fo["out_rh"]), fo["label"])
            if fkey != self._last_forecast_key:
                self._last_forecast_key = fkey
                if self._on_forecast:
                    self._on_forecast(fo)
            with self._lock:
                mode, desired, reason = self._compute(fo)
                self._desired = desired
                self._mode = mode
                self._reason = reason
                # gradual ramp: ease current toward desired, bounded per tick
                max_delta = self._step * self._tick
                if desired > self._current:
                    self._current = min(desired, self._current + max_delta)
                elif desired < self._current:
                    self._current = max(desired, self._current - max_delta)
                st = self._state_locked()
                # emit only on a meaningful change (mode, ~2% effort, or reason)
                key = (st["mode"], st["percent"] // 2, st["reason"], st["override"])
                changed = key != self._last_emit_key
                if changed:
                    self._last_emit_key = key
            if changed and self._on_state:
                self._on_state(st)
            time.sleep(self._tick)
