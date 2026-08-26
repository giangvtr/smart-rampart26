"""
Local, zero-install logging: SQLite (stdlib) + a daily CSV mirror.

No database server to install minutes before a presentation -- SQLite is a
single file, and the CSV opens in Excel/pandas. Three things get logged:

  * every Reading                    -> table `readings`  + daily CSV
  * every alarm state transition     -> table `events`
  * every agent override/login action-> table `audit`

Also keeps per-sensor in-memory ring buffers that feed the live plots (so the
UI never has to hit the DB to redraw).
"""
from __future__ import annotations

import csv
import os
import sqlite3
import threading
import time
from collections import deque
from datetime import datetime

import config
from core import Reading


class RingBuffer:
    """Fixed-size (timestamp, value, state) history for one sensor."""

    def __init__(self, maxpoints: int = config.RING_BUFFER_POINTS):
        self._t = deque(maxlen=maxpoints)
        self._v = deque(maxlen=maxpoints)
        self._s = deque(maxlen=maxpoints)

    def append(self, ts: float, value: float, state: str) -> None:
        self._t.append(ts)
        self._v.append(value)
        self._s.append(state)

    def arrays(self):
        """Return (times, values) as plain lists (pyqtgraph / JSON)."""
        return list(self._t), list(self._v)

    @property
    def last_state(self) -> str | None:
        return self._s[-1] if self._s else None

    @property
    def last_value(self) -> float | None:
        return self._v[-1] if self._v else None


class Storage:
    """SQLite + CSV writer and in-memory buffers. Thread-safe for the writer."""

    def __init__(self, db_path: str = config.DB_PATH, csv_dir: str = config.CSV_DIR):
        self.db_path = db_path
        self.csv_dir = csv_dir
        os.makedirs(csv_dir, exist_ok=True)

        # check_same_thread=False: readings arrive from a transport QThread while
        # the GUI thread also queries; we serialise every write with a lock.
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self._init_schema()

        self.buffers: dict[str, RingBuffer] = {s.key: RingBuffer() for s in config.SENSORS}
        self._last_state: dict[str, str] = {}
        self._csv_day: str | None = None
        self._csv_file = None
        self._csv_writer = None

    # -- schema -----------------------------------------------------------
    def _init_schema(self) -> None:
        with self._lock:
            self._db.executescript(
                """
                CREATE TABLE IF NOT EXISTS readings (
                    ts REAL, zone TEXT, sensor TEXT, value REAL, state TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(ts);
                CREATE TABLE IF NOT EXISTS events (
                    ts REAL, zone TEXT, sensor TEXT, value REAL,
                    old_state TEXT, new_state TEXT
                );
                CREATE TABLE IF NOT EXISTS audit (
                    ts REAL, actor TEXT, action TEXT, detail TEXT
                );
                """
            )
            self._db.commit()

    # -- CSV rotation -----------------------------------------------------
    def _csv_for_today(self):
        day = datetime.now().strftime("%Y-%m-%d")
        if day != self._csv_day:
            if self._csv_file:
                self._csv_file.close()
            path = os.path.join(self.csv_dir, f"readings-{day}.csv")
            new = not os.path.exists(path)
            self._csv_file = open(path, "a", newline="", encoding="utf-8")
            self._csv_writer = csv.writer(self._csv_file)
            if new:
                self._csv_writer.writerow(["iso_time", "ts", "zone", "sensor", "value", "state"])
            self._csv_day = day
        return self._csv_writer

    # -- writes -----------------------------------------------------------
    def record_reading(self, r: Reading) -> str | None:
        """Persist a reading + buffer it. Returns the previous state if it
        changed (so the caller can flag a transition), else None."""
        buf = self.buffers.get(r.key)
        if buf is not None:
            buf.append(r.ts, r.value, r.state)

        prev = self._last_state.get(r.key)
        changed = prev is not None and prev != r.state
        self._last_state[r.key] = r.state

        with self._lock:
            self._db.execute(
                "INSERT INTO readings VALUES (?,?,?,?,?)",
                (r.ts, r.zone, r.sensor, r.value, r.state),
            )
            if changed:
                self._db.execute(
                    "INSERT INTO events VALUES (?,?,?,?,?,?)",
                    (r.ts, r.zone, r.sensor, r.value, prev, r.state),
                )
            self._db.commit()
            writer = self._csv_for_today()
            writer.writerow([
                datetime.fromtimestamp(r.ts).isoformat(timespec="seconds"),
                f"{r.ts:.3f}", r.zone, r.sensor, f"{r.value:g}", r.state,
            ])
            self._csv_file.flush()

        return prev if changed else None

    def record_audit(self, actor: str, action: str, detail: str = "") -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO audit VALUES (?,?,?,?)",
                (time.time(), actor, action, detail),
            )
            self._db.commit()

    def close(self) -> None:
        with self._lock:
            if self._csv_file:
                self._csv_file.close()
            self._db.close()
