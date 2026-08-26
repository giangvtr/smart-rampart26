"""
Unsupervised anomaly detection over the live sensor streams.

This is the MuseumGuard equivalent of LoadRunner Analysis' anomaly detection:
nothing here is configured per-sensor by hand. The engine *learns* what normal
looks like for each stream from the stream itself, then flags the time windows
that stop matching it. Those windows are shaded on the graph and listed in the
"Anomalies" pane, exactly like LoadRunner shades an anomalous region and lets
you click it to jump there.

Why this is not the same thing as the warn/alarm bands in config.py
-------------------------------------------------------------------
Those bands are *static thresholds*: "humidity above 65 %RH is an alarm". They
say nothing about a sensor that jumps 3 degrees in one sample and holds there
while staying inside its safe band, or one that flatlines because its wiring
came loose. Anomaly detection is about the *shape* of the series, so the two
are complementary -- an anomaly window will often sit right next to a red
threshold band, and that is fine.

Method
------
Everything is built on robust statistics (median / MAD) rather than mean and
standard deviation, because a single spike moves a mean but barely moves a
median -- so the baseline does not learn the very excursion we want to catch.

    sigma = 1.4826 * MAD          (the MAD-to-stddev scale factor for a normal)
    z     = |x - median| / sigma

Two streams are watched at once, which is what lets us tell *how* a stream
went wrong rather than just *that* it did:

  * the **level**  -- the value against the learned baseline. Catches anything
    sustained, however gradually it got there.
  * the **first difference** (x[n] - x[n-1]) -- catches abrupt onsets. This
    matters because the environmental sensors wander like a random walk, and a
    random walk's level drifts far enough over a window to blur a step change;
    differencing removes that drift and makes the step obvious.

On top of the point-wise tests sit three "condition" detectors that no single
sample can reveal: a flatline (variance collapses -- a stuck sensor), a noise
burst (variance explodes) and a trend drift (sustained monotonic movement).

Only samples believed to be normal train the baseline, so an anomaly in
progress cannot quietly redefine "normal" underneath itself. A window that
stays open past ``max_open_s`` is closed and the new level is adopted -- a
permanent step is an anomaly once, not forever.

The module is frontend-agnostic (stdlib only, no Qt, no numpy): both the web
server and the desktop app feed it the same `Reading`s.
"""
from __future__ import annotations

import itertools
import math
import statistics
import threading
from collections import deque
from dataclasses import dataclass, field

import config

# Human labels for the kinds the engine can report.
KIND_LABELS = {
    "spike": "Spike",
    "step": "Level shift",
    "excursion": "Sustained deviation",
    "drift": "Trend drift",
    "flatline": "Flatlined",
    "noise": "Noise burst",
}

SEV_LOW, SEV_MEDIUM, SEV_HIGH = "LOW", "MEDIUM", "HIGH"
SEV_ORDER = {SEV_LOW: 0, SEV_MEDIUM: 1, SEV_HIGH: 2}
_SEV_BY_RANK = [SEV_LOW, SEV_MEDIUM, SEV_HIGH]

_ids = itertools.count(1)


def _mad_sigma(values, center: float) -> float:
    """Robust stand-in for the standard deviation: 1.4826 * median|x - center|."""
    if len(values) < 2:
        return 0.0
    return 1.4826 * statistics.median([abs(v - center) for v in values])


def _linear_fit(xs, ys):
    """Least-squares slope + R^2. Returns (slope, r2); slope is per x-unit."""
    n = len(xs)
    if n < 3:
        return 0.0, 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    r2 = (sxy * sxy) / (sxx * syy)
    return slope, r2


# --------------------------------------------------------------------------
# One detected window
# --------------------------------------------------------------------------
@dataclass
class Anomaly:
    """One anomalous time window on one sensor.

    Mutable on purpose: a window is *opened* on the first offending sample and
    keeps growing (end time, peak deviation) until the stream behaves again, so
    the UI can shade it live rather than only after the fact.
    """
    id: int
    key: str
    kind: str
    t_start: float
    t_end: float
    baseline: float          # what "normal" was when the window opened
    peak_value: float        # the most extreme sample inside the window
    peak_z: float            # its robust z-score
    direction: str           # "above" | "below" | "" (for flatline/noise)
    open: bool = True
    detail: dict = field(default_factory=dict)   # kind-specific extras

    @property
    def duration(self) -> float:
        return max(0.0, self.t_end - self.t_start)

    @property
    def severity(self) -> str:
        rank = 0 if self.peak_z < 5.0 else (1 if self.peak_z < 8.0 else 2)
        # something that *stays* wrong is worse than the same excursion in a blip
        if self.kind in ("step", "excursion", "flatline", "drift") and self.duration >= 45.0:
            rank += 1
        return _SEV_BY_RANK[min(rank, 2)]

    @property
    def confidence(self) -> float:
        """0..1, saturating -- "how sure are we this is not noise"."""
        excess = max(0.0, self.peak_z - 3.0)
        return round(min(0.99, 1.0 - 2.718281828 ** (-excess / 2.5)), 2)

    def message(self, sdef) -> str:
        u = sdef.unit
        d = self.duration
        if self.kind == "flatline":
            return (f"Stuck at {self.peak_value:g} {u} for {d:.0f} s "
                    f"— no variation at all; check the sensor or its wiring")
        if self.kind == "noise":
            return (f"Spread {self.detail.get('factor', 0):.1f}x the learned baseline "
                    f"for {d:.0f} s — unstable reading")
        if self.kind == "drift":
            net = self.detail.get("net", 0.0)
            return (f"Drifting {net:+.2f} {u} over {d:.0f} s "
                    f"(R²={self.detail.get('r2', 0):.2f}) — sustained one-way movement")
        verb = {"spike": "Spike", "step": "Level shift", "excursion": "Deviation"}[self.kind]
        held = f" held for {d:.0f} s" if self.kind != "spike" else ""
        return (f"{verb} to {self.peak_value:g} {u}{held} — {self.peak_z:.1f}σ "
                f"{self.direction} the {self.baseline:g} {u} baseline")

    def to_dict(self, sdef) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "zone": sdef.zone,
            "label": sdef.label,
            "unit": sdef.unit,
            "kind": self.kind,
            "kindLabel": KIND_LABELS.get(self.kind, self.kind),
            "t0": round(self.t_start, 3),
            "t1": round(self.t_end, 3),
            "duration": round(self.duration, 1),
            "open": self.open,
            "severity": self.severity,
            "score": round(self.peak_z, 2),
            "confidence": self.confidence,
            "baseline": round(self.baseline, 3),
            "peak": self.peak_value,
            "message": self.message(sdef),
        }


# --------------------------------------------------------------------------
# Per-sensor detector
# --------------------------------------------------------------------------
class SensorDetector:
    """Learns one sensor's normal behaviour and reports its anomalous windows.

    Holds at most two open windows at a time: one from the point-wise tests
    (spike / step / excursion) and one from the condition tests (flatline /
    noise / drift). They are independent -- a sensor can be drifting *and*
    spike -- but two overlapping windows of the same family would just be one
    window, so each family keeps a single open record.
    """

    def __init__(self, sdef, cfg: dict):
        self.sdef = sdef
        self.cfg = cfg
        self.enabled = getattr(sdef, "detect_anomalies", True)

        # every sample in the recent past (both normal and not) -- the condition
        # detectors need the raw shape, including the anomalous parts
        self._t: deque[float] = deque()
        self._v: deque[float] = deque()
        # only the samples believed normal -- this is what trains the baseline
        self._clean: deque[float] = deque()
        self._clean_t: deque[float] = deque()
        self._deltas: deque[float] = deque()

        # how much raw history the condition detectors need behind them
        self._horizon = max(cfg["baseline_window_s"] * 2, cfg["drift_window_s"],
                            cfg["flatline_min_s"], cfg["noise_min_s"]) + 15.0

        self.center: float | None = None
        self.sigma: float = 0.0
        self._dsig: float = 0.0        # spread of the sample-to-sample steps
        self._lag: int = 1             # samples since one last trained the baseline
        self._last_value: float | None = None
        self._last_ts: float | None = None

        self.open_point: Anomaly | None = None
        self.open_cond: Anomaly | None = None

        # the learned expected range, sampled alongside the readings so the
        # chart can draw it as a ribbon behind the trace
        keep = config.RING_BUFFER_POINTS
        self.band_t: deque[float] = deque(maxlen=keep)
        self.band_lo: deque[float] = deque(maxlen=keep)
        self.band_hi: deque[float] = deque(maxlen=keep)

    # -- helpers ----------------------------------------------------------
    @property
    def _sigma_floor(self) -> float:
        span = float(self.sdef.vmax - self.sdef.vmin)
        return max(span * self.cfg["min_sigma_frac"], 1e-9)

    def _warm(self) -> bool:
        return len(self._clean) >= self.cfg["min_baseline_points"]

    def _delta_sigma(self) -> float:
        """Robust spread of the sample-to-sample step, from clean samples only."""
        if len(self._deltas) < 8:
            return self._sigma_floor
        return max(_mad_sigma(self._deltas, statistics.median(self._deltas)),
                   self._sigma_floor)

    def _recent(self, seconds: float):
        """(times, values) for the last `seconds` of raw samples."""
        cutoff = self._t[-1] - seconds if self._t else 0.0
        ts, vs = [], []
        for t, v in zip(self._t, self._v):
            if t >= cutoff:
                ts.append(t)
                vs.append(v)
        return ts, vs

    def _rebaseline(self) -> None:
        """Adopt the current level as the new normal.

        Called when a window has been open long enough to count as the stream's
        new normal rather than an excursion from the old one. Without this a
        permanent step would keep every later sample "anomalous" forever.
        """
        ts, vs = self._recent(self.cfg["max_open_s"] * 0.8)
        self._clean.clear()
        self._clean_t.clear()
        self._clean.extend(vs)
        self._clean_t.extend(ts)

    def _trim_clean(self, ts: float) -> None:
        """Age out baseline samples, but never below the warm-up minimum."""
        floor_n = self.cfg["min_baseline_points"]
        cutoff = ts - self.cfg["baseline_window_s"]
        while len(self._clean) > floor_n and self._clean_t[0] < cutoff:
            self._clean.popleft()
            self._clean_t.popleft()
        while len(self._deltas) > floor_n * 3:
            self._deltas.popleft()

    # -- main entry point --------------------------------------------------
    def feed(self, ts: float, value: float) -> list[Anomaly]:
        """Absorb one sample; return the windows that opened, grew or closed."""
        if not self.enabled:
            return []

        changed: list[Anomaly] = []
        cfg = self.cfg

        self._t.append(ts)
        self._v.append(value)
        while self._t and self._t[0] < ts - self._horizon:
            self._t.popleft()
            self._v.popleft()

        # ---- score the sample against what we have learned so far ---------
        #
        # The level test cannot simply be |x - median| / MAD. These streams
        # wander, so the longer the baseline goes without a fresh clean sample
        # (which is exactly what happens while a window is open), the further a
        # perfectly innocent walk will have strayed from it -- and a fixed MAD
        # would read that growing gap as a growing anomaly. So the yardstick
        # grows too, by how far a driftless walk could have gone in the same
        # number of steps: sqrt(lag) * the per-step spread. A real step change
        # outruns that; a wander never does.
        self._dsig = dsig = self._delta_sigma()
        lag = min(self._lag, 60)
        z = dz = 0.0
        if self._warm():
            sigma_eff = math.sqrt(max(self.sigma, self._sigma_floor) ** 2
                                  + dsig * dsig * lag)
            z = abs(value - self.center) / sigma_eff
            if self._last_value is not None and len(self._deltas) >= 8:
                dcenter = statistics.median(self._deltas)
                dz = abs((value - self._last_value) - dcenter) / dsig

        abrupt = dz >= cfg["delta_z"]
        anomalous = self._warm() and (z >= cfg["level_z"] or abrupt)

        # ---- point-wise window bookkeeping --------------------------------
        # A flatline or a noise burst *is* the anomaly; while one of those is
        # open, its samples would also trip the point-wise test over and over
        # and bury the real finding under a stream of one-off spikes.
        suppressed = self.open_cond is not None and self.open_point is None

        if anomalous and not suppressed:
            a = self.open_point
            if a is None:
                a = Anomaly(
                    id=next(_ids), key=self.sdef.key, kind="spike", t_start=ts,
                    t_end=ts, baseline=round(self.center, 3), peak_value=value,
                    peak_z=max(z, dz),
                    direction="above" if value >= self.center else "below",
                )
                a.detail["abrupt"] = abrupt
                self.open_point = a
            a.t_end = ts
            a.peak_z = max(a.peak_z, z, dz)
            # "peak" means furthest from the baseline, judged on the level. Not
            # on the step score: coming back down from a spike is just as abrupt
            # as going up, so scoring by dz would report the recovery sample as
            # the peak and flip the direction with it.
            if abs(value - a.baseline) > abs(a.peak_value - a.baseline):
                a.peak_value = value
                a.direction = "above" if value >= a.baseline else "below"
            a.kind = self._classify(a)
            changed.append(a)

            # A window that stays open this long is not an excursion from the
            # old normal any more -- it IS the new normal. Close it (the shape
            # change is what we wanted to report) and relearn around the new
            # level, so the rest of the run is judged against where the stream
            # actually is. Whether that new level is *safe* is the job of the
            # warn/alarm thresholds in config.py, not of this detector.
            if a.duration >= cfg["max_open_s"]:
                a.open = False
                self.open_point = None
                self._rebaseline()
                self._lag = 1          # the baseline is fresh again
            else:
                self._lag += 1
        else:
            # only quiet samples are allowed to teach the baseline
            self._clean.append(value)
            self._clean_t.append(ts)
            if self._last_value is not None and self._lag == 1:
                # a step across a gap in clean samples is not a clean step
                self._deltas.append(value - self._last_value)
            self._trim_clean(ts)
            self._lag = 1

            a = self.open_point
            if a is not None and ts - a.t_end >= cfg["close_after_s"]:
                a.open = False
                a.kind = self._classify(a)
                self.open_point = None
                changed.append(a)

        # ---- refresh the baseline + the expected-range ribbon -------------
        if self._clean:
            self.center = statistics.median(self._clean)
            self.sigma = max(_mad_sigma(self._clean, self.center), self._sigma_floor)
            if self._warm():
                half = self.sigma * self.cfg["level_z"]
                self.band_t.append(round(ts, 3))
                self.band_lo.append(round(self.center - half, 3))
                self.band_hi.append(round(self.center + half, 3))

        # ---- condition detectors ------------------------------------------
        changed.extend(self._check_conditions(ts))

        self._last_value = value
        self._last_ts = ts
        return changed

    def _classify(self, a: Anomaly) -> str:
        """Name the window from how long it lasted and how abruptly it began."""
        d = a.duration
        if d < self.cfg["spike_max_s"]:
            return "spike"
        if d >= self.cfg["shift_min_s"] and a.detail.get("abrupt"):
            return "step"
        return "excursion"

    # -- flatline / noise / drift -----------------------------------------
    def _check_conditions(self, ts: float) -> list[Anomaly]:
        cfg = self.cfg
        changed: list[Anomaly] = []
        if not self._warm():
            return changed

        kind, peak_z, detail = None, 0.0, {}
        floor = self._sigma_floor

        flat_ts, flat_vs = self._recent(cfg["flatline_min_s"])
        win_ts, win_vs = self._recent(cfg["noise_min_s"])
        drift_ts, drift_vs = self._recent(cfg["drift_window_s"])

        # 1. flatline -- a stream that normally moves has stopped moving at all.
        #
        # "Stopped moving" is measured against this stream's own per-sample step,
        # NOT against the sigma floor. The floor is a fraction of the y-axis
        # range, and a wide-range sensor (light: 0-1023 adc) drifts far less than
        # that in normal service -- judged by the floor, a perfectly healthy
        # light reading looks stuck.
        #
        # The "normally moves" half has to come from before the flat stretch:
        # once a sensor sticks, the learned spread collapses within one baseline
        # window and would happily vouch for the stuck value as normal.
        prior_vs = [v for t, v in zip(self._t, self._v)
                    if t < ts - cfg["flatline_min_s"]]
        prior_steps = [b - a for a, b in zip(prior_vs, prior_vs[1:])]
        if (len(flat_vs) >= 8
                and flat_ts[-1] - flat_ts[0] >= cfg["flatline_min_s"] * 0.9
                and max(flat_vs) - min(flat_vs) <= self._dsig * cfg["flatline_frac"]
                and len(prior_steps) >= 8
                and _mad_sigma(prior_steps, statistics.median(prior_steps)) > 0):
            kind, peak_z = "flatline", 6.0
            detail = {}

        # 2. noise burst -- per-sample jitter has blown out. Measured on the
        # steps, not the levels: a wandering stream's *level* spread grows with
        # the window length all by itself, so comparing levels would call a
        # long quiet wander a noise burst.
        elif len(win_vs) >= 8 and win_ts[-1] - win_ts[0] >= cfg["noise_min_s"] * 0.9:
            steps = [b - a for a, b in zip(win_vs, win_vs[1:])]
            recent = _mad_sigma(steps, statistics.median(steps))
            factor = recent / max(self._dsig, floor)
            if factor >= cfg["noise_factor"]:
                kind, peak_z = "noise", 3.0 + factor
                detail = {"factor": round(factor, 2)}

        # 3. drift -- sustained one-way movement, well beyond a random wander
        #
        # The bar here has to be a *random-walk* bar, not a fixed multiple of the
        # level's spread. These streams wander, and a wander fits a straight line
        # deceptively well (R^2 around 0.85 is routine for a driftless walk), so
        # R^2 alone flags noise as trend. What separates the two is distance
        # travelled: over n steps of per-step spread `dsig`, a driftless walk ends
        # up about dsig*sqrt(n) from where it started, while a real drift goes
        # linearly further. Requiring drift_k times that random-walk expectation
        # is the test that actually discriminates.
        if kind is None and len(drift_vs) >= 12 and drift_ts[-1] - drift_ts[0] >= cfg["drift_window_s"] * 0.9:
            t0 = drift_ts[0]
            slope, r2 = _linear_fit([t - t0 for t in drift_ts], drift_vs)
            net = slope * (drift_ts[-1] - t0)
            steps = [b - a for a, b in zip(drift_vs, drift_vs[1:])]
            dsig = max(_mad_sigma(steps, statistics.median(steps)), floor)
            expected = dsig * (len(steps) ** 0.5)      # a driftless walk's reach
            if r2 >= cfg["drift_r2"] and abs(net) >= cfg["drift_k"] * expected:
                kind = "drift"
                peak_z = abs(net) / expected
                detail = {"net": round(net, 3), "r2": round(r2, 3),
                          "slope": round(slope, 5)}

        a = self.open_cond
        if kind is None:
            if a is not None and ts - a.t_end >= self.cfg["close_after_s"]:
                a.open = False
                self.open_cond = None
                changed.append(a)
            return changed

        peak = self._v[-1]
        if a is None or a.kind != kind:
            if a is not None:                       # one condition replaced another
                a.open = False
                changed.append(a)
            # the window started when the condition did, not when we noticed it
            span = {"flatline": cfg["flatline_min_s"], "noise": cfg["noise_min_s"],
                    "drift": cfg["drift_window_s"]}[kind]
            a = Anomaly(
                id=next(_ids), key=self.sdef.key, kind=kind, t_start=ts - span,
                t_end=ts, baseline=round(self.center, 3), peak_value=peak,
                peak_z=peak_z, direction="",
            )
            self.open_cond = a
        a.t_end = ts
        a.peak_value = peak
        a.peak_z = max(a.peak_z, peak_z)
        a.detail.update(detail)
        changed.append(a)
        return changed


# --------------------------------------------------------------------------
# Engine -- one detector per sensor + the rolling list of what was found
# --------------------------------------------------------------------------
class AnomalyEngine:
    """Owns a `SensorDetector` per configured sensor and the anomaly history.

    Thread-safe: `feed` runs on the transport thread while HTTP threads read
    `recent()` / `bands()` to answer a bootstrap.
    """

    def __init__(self, cfg: dict | None = None, enabled: bool | None = None):
        self.cfg = dict(config.ANOMALY)
        if cfg:
            self.cfg.update(cfg)
        self.enabled = config.ANOMALY_ENABLED if enabled is None else enabled
        self._lock = threading.Lock()
        self.detectors: dict[str, SensorDetector] = {
            s.key: SensorDetector(s, self.cfg) for s in config.SENSORS
        }
        self._by_id: dict[int, Anomaly] = {}
        self._order: deque[int] = deque()      # insertion order, oldest first

    # -- write -------------------------------------------------------------
    def feed(self, reading) -> list[dict]:
        """Absorb one Reading; return the anomaly records that changed, as
        JSON-ready dicts (newly opened, grown, or just closed)."""
        if not self.enabled:
            return []
        det = self.detectors.get(reading.key)
        if det is None:
            return []
        with self._lock:
            changed = det.feed(reading.ts, reading.value)
            out = []
            for a in changed:
                if a.id not in self._by_id:
                    self._by_id[a.id] = a
                    self._order.append(a.id)
                    while len(self._order) > self.cfg["keep"]:
                        self._by_id.pop(self._order.popleft(), None)
                out.append(a.to_dict(det.sdef))
            return out

    # -- read --------------------------------------------------------------
    def recent(self, limit: int = 60) -> list[dict]:
        """The most recent anomalies, newest first."""
        with self._lock:
            ids = list(self._order)[-limit:]
            return [self._by_id[i].to_dict(self.detectors[self._by_id[i].key].sdef)
                    for i in reversed(ids) if i in self._by_id]

    def band(self, key: str) -> dict | None:
        """The learned expected-range ribbon for one sensor, for the chart."""
        det = self.detectors.get(key)
        if det is None or not det.band_t:
            return None
        with self._lock:
            return {"t": list(det.band_t), "lo": list(det.band_lo),
                    "hi": list(det.band_hi)}

    def current_band(self, key: str) -> list[float] | None:
        """The latest [lo, hi] expected range, to ride along with a reading."""
        det = self.detectors.get(key)
        if det is None or not det.band_t:
            return None
        return [det.band_lo[-1], det.band_hi[-1]]

    def summary(self) -> dict:
        """Counts by severity over the retained window -- for the header pill."""
        with self._lock:
            counts = {SEV_LOW: 0, SEV_MEDIUM: 0, SEV_HIGH: 0}
            openn = 0
            for i in self._order:
                a = self._by_id.get(i)
                if a is None:
                    continue
                counts[a.severity] += 1
                openn += 1 if a.open else 0
            return {"total": len(self._order), "open": openn, "bySeverity": counts}
