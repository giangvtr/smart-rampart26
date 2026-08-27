"""
Weather-forecast feedforward for the HVAC controller.

Standard HVAC is reactive -- it conditions only after a threshold is breached. A
predictive system looks at the *outdoor* outlook and acts early: pre-emptively
dehumidifying before a forecast humid spell, or coasting on passive building mass
when the outdoor trend will pull conditions back on its own.

This module abstracts "what is the near-term outdoor outlook" behind a tiny
`ForecastSource` interface, mirroring the transport swap in transports.py:

    SimulatedForecast  -- default; a slow synthetic swing, fully offline, so the
                          demo visibly shows pre-emptive action with no network.
    HttpForecast       -- optional; pulls Open-Meteo (no API key) when online and
                          falls back to the sim outlook on any failure.

`outlook()` returns a dict the controller reads:

    { "trend": "warming"|"cooling"|"steady",
      "out_temp_c": float, "out_rh": float,      # near-term outdoor conditions
      "d_temp_c": float,  "d_rh": float,          # expected change vs now (signed)
      "horizon_h": float, "label": str }          # human-readable summary
"""
from __future__ import annotations

import json
import math
import threading
import time
import urllib.request


class ForecastSource:
    """Base interface. Subclasses override start/stop/outlook."""

    def start(self) -> None:  # pragma: no cover - interface
        pass

    def stop(self) -> None:   # pragma: no cover - interface
        pass

    def outlook(self) -> dict:  # pragma: no cover - interface
        raise NotImplementedError


class SimulatedForecast(ForecastSource):
    """Offline synthetic outlook. A slow sinusoid drives outdoor temp/RH over a
    ~10 min period so the demo shows the controller pre-empting a 'heatwave' and a
    'cold front' within a short sitting, with no internet."""

    PERIOD_S = 600.0     # one full warm↔cool cycle every 10 minutes
    TEMP_MEAN = 22.0
    TEMP_SWING = 9.0     # outdoor temp roams 13..31 °C
    RH_MEAN = 55.0
    RH_SWING = 22.0      # outdoor RH roams 33..77 %RH (RH lags temp -> humid+warm)

    def __init__(self) -> None:
        self._t0 = time.time()

    def _phase(self, at: float) -> float:
        return 2 * math.pi * ((at - self._t0) % self.PERIOD_S) / self.PERIOD_S

    def outlook(self) -> dict:
        now = time.time()
        ph = self._phase(now)
        # Look a QUARTER-cycle ahead for the "3 h" delta. Using a literal +3 h
        # would land a whole number of PERIOD_S cycles later (same phase, zero
        # delta, trend forever "steady"); a quarter cycle gives a delta that
        # genuinely swings warming -> steady -> cooling as the demo runs.
        ph_next = self._phase(now + self.PERIOD_S * 0.25)
        out_temp = self.TEMP_MEAN + self.TEMP_SWING * math.sin(ph)
        out_rh = self.RH_MEAN + self.RH_SWING * math.sin(ph - 0.6)   # RH trails temp
        nxt_temp = self.TEMP_MEAN + self.TEMP_SWING * math.sin(ph_next)
        nxt_rh = self.RH_MEAN + self.RH_SWING * math.sin(ph_next - 0.6)
        d_temp = nxt_temp - out_temp
        d_rh = nxt_rh - out_rh
        trend = "warming" if d_temp > 0.5 else "cooling" if d_temp < -0.5 else "steady"
        label = {
            "warming": "Warm front approaching",
            "cooling": "Cooler air moving in",
            "steady": "Outdoor conditions steady",
        }[trend]
        return {
            "trend": trend, "out_temp_c": round(out_temp, 1), "out_rh": round(out_rh, 1),
            "d_temp_c": round(d_temp, 1), "d_rh": round(d_rh, 1),
            "horizon_h": 3.0, "label": label,
        }


class HttpForecast(ForecastSource):
    """Real outlook from Open-Meteo (keyless). Polls on a background thread and
    caches the last good outlook; any network failure transparently falls back to
    a SimulatedForecast so the controller never blocks or starves."""

    POLL_S = 900.0   # 15 min; forecasts do not change faster than that

    def __init__(self, lat: float = 48.86, lon: float = 2.34) -> None:
        self.lat, self.lon = lat, lon
        self._fallback = SimulatedForecast()
        self._cached: dict | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def outlook(self) -> dict:
        with self._lock:
            if self._cached is not None:
                return self._cached
        return self._fallback.outlook()

    def _loop(self) -> None:
        while self._running:
            try:
                self._poll()
            except Exception:
                pass   # keep the cached/fallback outlook; try again next cycle
            # sleep in small slices so stop() is responsive
            for _ in range(int(self.POLL_S)):
                if not self._running:
                    return
                time.sleep(1.0)

    def _poll(self) -> None:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={self.lat}&longitude={self.lon}"
            "&hourly=temperature_2m,relative_humidity_2m&forecast_days=1"
        )
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        temps = data["hourly"]["temperature_2m"]
        rhs = data["hourly"]["relative_humidity_2m"]
        out_temp, out_rh = float(temps[0]), float(rhs[0])
        nxt_temp, nxt_rh = float(temps[min(3, len(temps) - 1)]), float(rhs[min(3, len(rhs) - 1)])
        d_temp, d_rh = nxt_temp - out_temp, nxt_rh - out_rh
        trend = "warming" if d_temp > 0.5 else "cooling" if d_temp < -0.5 else "steady"
        outlook = {
            "trend": trend, "out_temp_c": round(out_temp, 1), "out_rh": round(out_rh, 1),
            "d_temp_c": round(d_temp, 1), "d_rh": round(d_rh, 1),
            "horizon_h": 3.0,
            "label": f"Forecast: {out_temp:.0f} °C / {out_rh:.0f} %RH, {trend}",
        }
        with self._lock:
            self._cached = outlook


def make_forecast(name: str = "sim") -> ForecastSource:
    """Swap-point mirroring server.make_source(). 'off' yields a steady no-op."""
    if name == "http":
        return HttpForecast()
    if name == "off":
        return _NullForecast()
    return SimulatedForecast()


class _NullForecast(ForecastSource):
    """No feedforward: a flat, steady outlook (purely reactive HVAC)."""

    def outlook(self) -> dict:
        return {"trend": "steady", "out_temp_c": 20.0, "out_rh": 50.0,
                "d_temp_c": 0.0, "d_rh": 0.0, "horizon_h": 3.0,
                "label": "Forecast feedforward disabled"}
