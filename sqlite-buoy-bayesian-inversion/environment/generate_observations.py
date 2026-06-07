"""Build the seeded SQLite buoy-observation database used by the task.

Runs at image-build time only (in a throwaway builder stage); the agent never
sees this script or the true calibration parameters. Each included buoy's raw
reading is generated so that, after the binding unit conversion, the cleaned
residual (converted reading minus the co-located reference) follows a
heteroscedastic, change-point drift model:

    residual(t) = offset + drift * t + drift_change * max(0, t - t_changepoint)
                  + noise,   noise ~ Normal(0, measurement_std(t)**2)

where t is elapsed days since the mission epoch, the drift rate changes at the
fleet servicing changepoint, and each observation carries its own (time-varying)
measurement standard deviation, stored in physical units in the database. The
inversion the task asks for must therefore be a weighted (heteroscedastic),
three-parameter Bayesian generalized-least-squares estimate — not a textbook
two-parameter ordinary regression. Excluded windows and non-included buoys still
carry plausible rows, so the rules must be applied procedurally.
"""

import math
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)
N_DAYS = 182  # 2024-01-01 .. 2024-06-30 inclusive (daily samples)
CHANGEPOINT = datetime(2024, 3, 17, tzinfo=timezone.utc)
T_CHANGE = (CHANGEPOINT - EPOCH).total_seconds() / 86400.0  # 76.0 days

UNIT_CONVERSION = {"temperature": 0.0625, "pressure": 0.1, "salinity": 0.001}
# Nominal (base) measurement noise per sensor type, in physical units. The actual
# per-observation measurement_std grows over the deployment (see below).
BASE_STD = {"temperature": 0.05, "pressure": 0.2, "salinity": 0.01}

# Fleet. Only active temperature/pressure buoys are calibrated; salinity (B005)
# and the retired unit (B006) are distractors. Each calibrated buoy has a true
# offset, a baseline drift, and a post-changepoint drift change.
BUOYS = [
    {"buoy_id": "B001", "name": "Sentinel-North", "sensor_type": "temperature", "status": "active", "raw_units": "counts", "offset": 0.30, "drift": 0.0015, "drift_change": -0.0025},
    {"buoy_id": "B002", "name": "Sentinel-East", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": -1.50, "drift": 0.030, "drift_change": -0.050},
    {"buoy_id": "B003", "name": "Sentinel-South", "sensor_type": "temperature", "status": "active", "raw_units": "counts", "offset": 0.45, "drift": -0.0010, "drift_change": 0.0030},
    {"buoy_id": "B004", "name": "Sentinel-West", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": 2.20, "drift": -0.020, "drift_change": 0.040},
    {"buoy_id": "B005", "name": "Halocline-1", "sensor_type": "salinity", "status": "active", "raw_units": "counts", "offset": 0.10, "drift": 0.001, "drift_change": 0.0},
    {"buoy_id": "B006", "name": "Sentinel-Relic", "sensor_type": "temperature", "status": "retired", "raw_units": "counts", "offset": 0.90, "drift": 0.004, "drift_change": 0.0},
    {"buoy_id": "B007", "name": "Sentinel-Drift", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": 0.80, "drift": 0.015, "drift_change": -0.030},
]


def reference_signal(sensor_type, t):
    """Deterministic trusted co-located reference reading at t days past epoch."""
    if sensor_type == "temperature":
        return 15.0 + 6.0 * math.sin(2 * math.pi * t / 365.0) + 0.5 * math.cos(2 * math.pi * t / 30.0)
    if sensor_type == "pressure":
        return 1020.0 + 8.0 * math.sin(2 * math.pi * t / 180.0) + 1.5 * math.sin(2 * math.pi * t / 14.0)
    return 35.0 + 0.4 * math.sin(2 * math.pi * t / 90.0)


def measurement_std(sensor_type, t):
    """Per-observation measurement std (physical units): grows over the season so
    that down-weighting the noisier late observations materially changes the
    estimate (an unweighted fit gets a different, wrong answer)."""
    return BASE_STD[sensor_type] * (0.5 + 3.5 * (t / (N_DAYS - 1)))


def main(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE buoys (buoy_id TEXT PRIMARY KEY, name TEXT, sensor_type TEXT, "
        "status TEXT, raw_units TEXT)"
    )
    cur.execute(
        "CREATE TABLE observations (obs_id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "buoy_id TEXT, timestamp TEXT, raw_reading REAL, reference_reading REAL, "
        "measurement_std REAL)"
    )

    for i, buoy in enumerate(BUOYS):
        cur.execute(
            "INSERT INTO buoys VALUES (?, ?, ?, ?, ?)",
            (buoy["buoy_id"], buoy["name"], buoy["sensor_type"], buoy["status"], buoy["raw_units"]),
        )
        rng = np.random.default_rng(2024_0601 + i)
        scale = UNIT_CONVERSION[buoy["sensor_type"]]
        rows = []
        for day in range(N_DAYS):
            t = float(day)
            ts = (EPOCH + timedelta(days=day)).strftime("%Y-%m-%dT%H:%M:%SZ")
            reference = reference_signal(buoy["sensor_type"], t)
            std = measurement_std(buoy["sensor_type"], t)
            hinge = max(0.0, t - T_CHANGE)
            noise = float(rng.normal(0.0, std))
            converted = (
                reference
                + buoy["offset"]
                + buoy["drift"] * t
                + buoy["drift_change"] * hinge
                + noise
            )
            raw = converted / scale
            rows.append((buoy["buoy_id"], ts, raw, reference, std))
        cur.executemany(
            "INSERT INTO observations (buoy_id, timestamp, raw_reading, reference_reading, "
            "measurement_std) VALUES (?, ?, ?, ?, ?)",
            rows,
        )

    con.commit()
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "observations.db")
