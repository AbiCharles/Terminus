"""Build the seeded SQLite buoy-observation database used by the task.

Runs at image-build time only (in a throwaway builder stage); the agent never
sees this script or the true drift/offset parameters. Each included buoy's raw
reading is generated so that, after the binding unit conversion, it equals the
co-located reference reading plus a constant offset, a linear drift in time, and
Gaussian observation noise:

    convert(raw) = reference + offset_true + drift_true * t_days + noise

so the cleaned residual (convert(raw) - reference) follows the linear model the
Bayesian inversion is expected to recover. Excluded maintenance windows and
non-included buoys still carry plausible rows, so the calibration rules must be
applied procedurally rather than inferred from the values.
"""

import math
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)
N_DAYS = 182  # 2024-01-01 .. 2024-06-30 inclusive (daily samples)

# Binding unit conversions (raw counts -> physical units) and noise, per sensor type.
UNIT_CONVERSION = {"temperature": 0.0625, "pressure": 0.1, "salinity": 0.001}
NOISE_STD = {"temperature": 0.05, "pressure": 0.2, "salinity": 0.01}

# Fleet. Only active buoys whose sensor_type is temperature or pressure are
# calibrated; salinity (B005) and the retired unit (B006) are distractors.
BUOYS = [
    {"buoy_id": "B001", "name": "Sentinel-North", "sensor_type": "temperature", "status": "active", "raw_units": "counts", "offset": 0.30, "drift": 0.0012},
    {"buoy_id": "B002", "name": "Sentinel-East", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": -1.50, "drift": 0.030},
    {"buoy_id": "B003", "name": "Sentinel-South", "sensor_type": "temperature", "status": "active", "raw_units": "counts", "offset": 0.45, "drift": -0.0008},
    {"buoy_id": "B004", "name": "Sentinel-West", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": 2.20, "drift": -0.020},
    {"buoy_id": "B005", "name": "Halocline-1", "sensor_type": "salinity", "status": "active", "raw_units": "counts", "offset": 0.10, "drift": 0.001},
    {"buoy_id": "B006", "name": "Sentinel-Relic", "sensor_type": "temperature", "status": "retired", "raw_units": "counts", "offset": 0.90, "drift": 0.004},
    {"buoy_id": "B007", "name": "Sentinel-Drift", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": 0.80, "drift": 0.015},
]


def reference_signal(sensor_type, t):
    """Deterministic trusted co-located reference reading at t days past epoch."""
    if sensor_type == "temperature":
        return 15.0 + 6.0 * math.sin(2 * math.pi * t / 365.0) + 0.5 * math.cos(2 * math.pi * t / 30.0)
    if sensor_type == "pressure":
        return 1020.0 + 8.0 * math.sin(2 * math.pi * t / 180.0) + 1.5 * math.sin(2 * math.pi * t / 14.0)
    return 35.0 + 0.4 * math.sin(2 * math.pi * t / 90.0)


def main(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE buoys (buoy_id TEXT PRIMARY KEY, name TEXT, sensor_type TEXT, "
        "status TEXT, raw_units TEXT)"
    )
    cur.execute(
        "CREATE TABLE observations (obs_id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "buoy_id TEXT, timestamp TEXT, raw_reading REAL, reference_reading REAL)"
    )

    for i, buoy in enumerate(BUOYS):
        cur.execute(
            "INSERT INTO buoys VALUES (?, ?, ?, ?, ?)",
            (buoy["buoy_id"], buoy["name"], buoy["sensor_type"], buoy["status"], buoy["raw_units"]),
        )
        rng = np.random.default_rng(2024_0601 + i)
        scale = UNIT_CONVERSION[buoy["sensor_type"]]
        noise_std = NOISE_STD[buoy["sensor_type"]]
        rows = []
        for day in range(N_DAYS):
            t = float(day)
            ts = (EPOCH + timedelta(days=day)).strftime("%Y-%m-%dT%H:%M:%SZ")
            reference = reference_signal(buoy["sensor_type"], t)
            noise = float(rng.normal(0.0, noise_std))
            converted = reference + buoy["offset"] + buoy["drift"] * t + noise
            raw = converted / scale
            rows.append((buoy["buoy_id"], ts, raw, reference))
        cur.executemany(
            "INSERT INTO observations (buoy_id, timestamp, raw_reading, reference_reading) "
            "VALUES (?, ?, ?, ?)",
            rows,
        )

    con.commit()
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "observations.db")
