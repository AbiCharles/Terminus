"""Build the seeded SQLite buoy-observation database used by the task.

Runs at image-build time only (in a throwaway builder stage); the agent never
sees this script or the true calibration parameters. Each included buoy's raw
reading is generated so that, after the binding unit conversion, the cleaned
residual (converted reading minus the co-located reference) follows a
heteroscedastic, MULTI-change-point drift model:

    residual(t) = offset + drift * t + sum_k drift_change_k * max(0, t - cp_k)
                  + noise,   noise ~ Normal(0, measurement_std(t)**2)

where t is elapsed days since the mission epoch, the drift rate is revised at
each of K fleet servicing changepoints cp_1..cp_K, and each observation carries
its own (time-varying) measurement standard deviation, stored in physical units
in the database. The inversion the task asks for is therefore a weighted
(heteroscedastic) (K+2)-parameter Bayesian generalized-least-squares estimate:
the (K+2)x(K+2) weighted normal-equations system must be solved generally (a
hand-coded 3x3 inverse no longer suffices). Excluded windows and non-included
buoys still carry plausible rows, so the rules must be applied procedurally.
"""

import math
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)
N_DAYS = 182  # 2024-01-01 .. 2024-06-30 inclusive (daily samples)

# K = 4 fleet servicing changepoints across the season.
CHANGEPOINTS = [
    datetime(2024, 2, 15, tzinfo=timezone.utc),
    datetime(2024, 3, 17, tzinfo=timezone.utc),
    datetime(2024, 4, 20, tzinfo=timezone.utc),
    datetime(2024, 5, 25, tzinfo=timezone.utc),
]
T_CHANGES = [(cp - EPOCH).total_seconds() / 86400.0 for cp in CHANGEPOINTS]  # 45, 76, 110, 145

UNIT_CONVERSION = {"temperature": 0.0625, "pressure": 0.1, "salinity": 0.001}
BASE_STD = {"temperature": 0.05, "pressure": 0.2, "salinity": 0.01}

# Fleet. Only active temperature/pressure buoys are calibrated; salinity (B005)
# and the retired unit (B006) are distractors. Each calibrated buoy has a true
# offset, a baseline drift, and a vector of K post-changepoint drift increments.
# Buoys whose drift genuinely changes at >=1 servicing (a drift_change CI that
# excludes zero) are ACCEPTED by the gate; the two with an all-zero drift_change
# vector (B003, B007) are REJECTED, partitioning the fleet non-trivially.
BUOYS = [
    {"buoy_id": "B001", "name": "Sentinel-North", "sensor_type": "temperature", "status": "active", "raw_units": "counts", "offset": 0.30, "drift": 0.0015, "drift_changes": [-0.0120, 0.0000, 0.0000, 0.0060]},
    {"buoy_id": "B002", "name": "Sentinel-East", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": -1.50, "drift": 0.030, "drift_changes": [-0.060, 0.000, 0.028, 0.000]},
    {"buoy_id": "B003", "name": "Sentinel-South", "sensor_type": "temperature", "status": "active", "raw_units": "counts", "offset": 0.45, "drift": -0.0010, "drift_changes": [0.0, 0.0, 0.0, 0.0]},
    {"buoy_id": "B004", "name": "Sentinel-West", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": 2.20, "drift": -0.020, "drift_changes": [0.045, 0.000, 0.000, -0.022]},
    {"buoy_id": "B005", "name": "Halocline-1", "sensor_type": "salinity", "status": "active", "raw_units": "counts", "offset": 0.10, "drift": 0.001, "drift_changes": [0.0, 0.0, 0.0, 0.0]},
    {"buoy_id": "B006", "name": "Sentinel-Relic", "sensor_type": "temperature", "status": "retired", "raw_units": "counts", "offset": 0.90, "drift": 0.004, "drift_changes": [0.0, 0.0, 0.0, 0.0]},
    {"buoy_id": "B007", "name": "Sentinel-Drift", "sensor_type": "pressure", "status": "active", "raw_units": "counts", "offset": 0.80, "drift": 0.015, "drift_changes": [0.0, 0.0, 0.0, 0.0]},
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
            drift_term = sum(
                dc * max(0.0, t - tc) for dc, tc in zip(buoy["drift_changes"], T_CHANGES)
            )
            noise = float(rng.normal(0.0, std))
            converted = reference + buoy["offset"] + buoy["drift"] * t + drift_term + noise
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
