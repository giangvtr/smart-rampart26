"""
Live "Time to Preservation" metric: Preservation Index (PI) + cumulative TWPI.

Museums care less about "is it 21 °C right now" than "at the conditions this room
actually sustains, how long before the collection ages chemically". This module
turns the temperature/humidity stream into two numbers the dashboard shows:

  * PI   -- instantaneous Preservation Index (years): the expected lifespan if
            the *current* temp/RH were held forever. Warm + humid -> small PI.
  * TWPI -- Time-Weighted Preservation Index (years): the effective PI given the
            whole history so far. It is the weighted harmonic mean of PI,

                TWPI = elapsed / Σ( Δt / PI_i )

            i.e. the single PI that would have consumed the same fraction of the
            collection's life over the elapsed time. This is the live "your
            artwork has ~X years at these conditions" headline.

The PI model is a self-contained Arrhenius decay law (see config.PRESERVATION and
`pi()` below) so it runs offline with no lookup tables. The constants are a
documented approximation, not certified IPI values -- see the note in config.py.

Fed the same canonical `Reading`s as the anomaly engine, from Hub._on_reading.
Kept transport-agnostic and framework-free, so it works under sim/serial/http and
under either frontend.
"""
from __future__ import annotations

import math
import threading
import time

import config

_KELVIN = 273.15


def pi(temp_c: float, rh: float) -> float:
    """Preservation Index in years for a steady (temp_c, rh).

    Arrhenius decay: rate k ∝ RH^m · exp(−Ea/RT), lifetime PI ∝ 1/k. Solved so
    the ideal anchor in config reads ~anchor_pi_years. Larger = ages slower.
    """
    p = config.PRESERVATION
    rh = max(p["min_rh"], float(rh))
    t_k = float(temp_c) + _KELVIN
    anchor_t_k = p["anchor_temp_c"] + _KELVIN
    ea_over_r = p["Ea_j_mol"] / p["R"]

    years = (
        p["anchor_pi_years"]
        * (p["anchor_rh"] / rh) ** p["rh_exponent_m"]
        * math.exp(ea_over_r * (1.0 / t_k - 1.0 / anchor_t_k))
    )
    return max(0.0, min(p["pi_max_years"], years))


def band(years: float) -> str:
    """Colour band for a PI/TWPI value: 'good' | 'watch' | 'poor'."""
    p = config.PRESERVATION
    if years >= p["good_years"]:
        return "good"
    if years >= p["watch_years"]:
        return "watch"
    return "poor"


class PreservationEngine:
    """Accumulates PI and TWPI from the live temp/humidity stream.

    Temperature and humidity arrive as *separate* Readings (different sensors,
    ~3 s apart), so we keep the last-seen of each and (re)compute whenever either
    updates and both are known. TWPI integrates Δt/PI over wall-clock time between
    updates. All state is in memory -- a restart resets TWPI, matching the rest of
    the server's in-memory model.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._temp: float | None = None
        self._rh: float | None = None
        self._started: float | None = None   # first paired sample time
        self._last_ts: float | None = None    # last time we advanced the integral
        self._sum_dt_over_pi = 0.0             # Σ Δt/PI   (years/years = fraction)
        self._elapsed = 0.0                    # Σ Δt      (years)
        self._pi: float | None = None
        self._twpi: float | None = None

    def feed(self, reading) -> dict | None:
        """Update from one Reading. Returns a broadcast dict when both channels
        are known (so the caller can push an SSE 'preservation' event), else None.

        DISCONNECTED/STALE samples carry no fresh environmental truth, so they are
        ignored -- TWPI simply does not advance while the node is dark.
        """
        sensor = reading.sensor.upper()
        if sensor not in ("TEMP", "HUMIDITY"):
            return None
        if reading.state in (config.STATE_DISCONNECTED, config.STATE_STALE):
            return None

        now = float(reading.ts)
        with self._lock:
            if sensor == "TEMP":
                self._temp = float(reading.value)
            else:
                self._rh = float(reading.value)
            if self._temp is None or self._rh is None:
                return None

            inst = pi(self._temp, self._rh)

            if self._last_ts is None:
                self._started = now
                self._last_ts = now
            else:
                dt = now - self._last_ts
                if dt > 0:
                    dt_years = dt / (365.25 * 24 * 3600)
                    # trapezoid on 1/PI would be marginally better; the prior PI
                    # held over the interval is plenty for a live readout
                    prev_pi = self._pi if self._pi is not None else inst
                    self._sum_dt_over_pi += dt_years / max(prev_pi, 1e-9)
                    self._elapsed += dt_years
                    self._last_ts = now

            self._pi = inst
            self._twpi = (
                self._elapsed / self._sum_dt_over_pi
                if self._sum_dt_over_pi > 0 else inst
            )
            return self._payload_locked(now)

    def snapshot(self) -> dict | None:
        """Current metric for /api/bootstrap and reconnect seeding, or None if no
        paired reading has arrived yet."""
        with self._lock:
            if self._pi is None:
                return None
            return self._payload_locked(time.time())

    # caller must hold the lock
    def _payload_locked(self, ts: float) -> dict:
        twpi = self._twpi if self._twpi is not None else self._pi
        return {
            "pi": round(self._pi, 1),
            "twpi": round(twpi, 1),
            "band": band(twpi),
            "temp": self._temp,
            "rh": self._rh,
            "ts": ts,
        }
