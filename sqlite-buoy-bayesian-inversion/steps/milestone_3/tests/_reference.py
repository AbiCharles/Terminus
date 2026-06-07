"""Independent reference implementation for the buoy calibration task.

Encodes the binding calibration protocol (the answer key for milestone 1) and
recomputes, directly from the SQLite store at /app/observations.db, the cleaned
residual series (milestone 2) and the conjugate Gaussian posterior for each
buoy's offset and drift (milestone 3). It never reads the agent's protocol.json
or /app/artifacts, so an agent cannot weaken verification by tampering with its
own outputs, and the agent has no access to this module at solve time.

The numbers here are the binding governing values from the mission notebook;
superseded earlier-revision values that appear in the notebook as distractors are
deliberately NOT used.
"""

import sqlite3
from datetime import datetime, timezone

import numpy as np

DB_PATH = "/app/observations.db"

MISSION_EPOCH = "2024-01-01T00:00:00Z"
TIME_UNIT = "days"
ACTIVE_STATUS = "active"
INCLUDED_SENSOR_TYPES = ["pressure", "temperature"]

UNIT_CONVERSION = {"temperature": 0.0625, "pressure": 0.1}
NOISE_STD = {"temperature": 0.05, "pressure": 0.2}
PRIORS = {
    "temperature": {"offset": {"mean": 0.0, "std": 0.5}, "drift": {"mean": 0.0, "std": 0.02}},
    "pressure": {"offset": {"mean": 0.0, "std": 2.0}, "drift": {"mean": 0.0, "std": 0.05}},
}
EXCLUSION_INTERVALS = [
    {"buoy_id": "ALL", "start": "2024-03-10T00:00:00Z", "end": "2024-03-17T00:00:00Z"},
    {"buoy_id": "B003", "start": "2024-05-01T00:00:00Z", "end": "2024-05-20T00:00:00Z"},
]

Z95 = 1.959963984540054  # standard-normal 97.5th percentile


def _parse(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


_EPOCH_DT = _parse(MISSION_EPOCH)


def expected_protocol():
    """The binding protocol that milestone 1 must extract into /app/protocol.json."""
    return {
        "mission_epoch": MISSION_EPOCH,
        "time_unit": TIME_UNIT,
        "active_status": ACTIVE_STATUS,
        "included_sensor_types": INCLUDED_SENSOR_TYPES,
        "sensors": {
            "temperature": {
                "unit_conversion": UNIT_CONVERSION["temperature"],
                "noise_std": NOISE_STD["temperature"],
                "priors": PRIORS["temperature"],
            },
            "pressure": {
                "unit_conversion": UNIT_CONVERSION["pressure"],
                "noise_std": NOISE_STD["pressure"],
                "priors": PRIORS["pressure"],
            },
        },
        "exclusion_intervals": EXCLUSION_INTERVALS,
    }


def included_buoys(db_path=DB_PATH):
    """Buoy ids to calibrate: active status and an included sensor type, sorted."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT buoy_id, sensor_type FROM buoys WHERE status = ? ORDER BY buoy_id",
            (ACTIVE_STATUS,),
        ).fetchall()
    finally:
        con.close()
    return [b for b, s in rows if s in INCLUDED_SENSOR_TYPES]


def buoy_sensor_type(buoy_id, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT sensor_type FROM buoys WHERE buoy_id = ?", (buoy_id,)
        ).fetchone()
    finally:
        con.close()
    return row[0] if row else None


def _is_excluded(buoy_id, ts_dt):
    for iv in EXCLUSION_INTERVALS:
        if iv["buoy_id"] in ("ALL", buoy_id):
            if _parse(iv["start"]) <= ts_dt < _parse(iv["end"]):
                return True
    return False


def clean_series(buoy_id, db_path=DB_PATH):
    """Cleaned residual series for a buoy: applies inclusion, exclusion windows and
    the unit conversion. Returns a dict of parallel lists ordered by timestamp."""
    sensor_type = buoy_sensor_type(buoy_id, db_path)
    scale = UNIT_CONVERSION[sensor_type]
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT timestamp, raw_reading, reference_reading FROM observations "
            "WHERE buoy_id = ? ORDER BY timestamp",
            (buoy_id,),
        ).fetchall()
    finally:
        con.close()
    out = {"timestamp": [], "t_days": [], "converted_value": [], "reference_value": [], "residual": []}
    for ts, raw, ref in rows:
        ts_dt = _parse(ts)
        if _is_excluded(buoy_id, ts_dt):
            continue
        converted = raw * scale
        t_days = (ts_dt - _EPOCH_DT).total_seconds() / 86400.0
        out["timestamp"].append(ts)
        out["t_days"].append(t_days)
        out["converted_value"].append(converted)
        out["reference_value"].append(ref)
        out["residual"].append(converted - ref)
    return out


def posterior(buoy_id, db_path=DB_PATH):
    """Conjugate Gaussian posterior for (offset, drift) plus calibration metrics."""
    sensor_type = buoy_sensor_type(buoy_id, db_path)
    series = clean_series(buoy_id, db_path)
    t = np.array(series["t_days"], dtype=np.float64)
    r = np.array(series["residual"], dtype=np.float64)
    n = t.shape[0]

    priors = PRIORS[sensor_type]
    m0 = np.array([priors["offset"]["mean"], priors["drift"]["mean"]], dtype=np.float64)
    s0_inv = np.diag([1.0 / priors["offset"]["std"] ** 2, 1.0 / priors["drift"]["std"] ** 2])
    sigma2 = NOISE_STD[sensor_type] ** 2

    design = np.column_stack([np.ones(n), t])
    sn = np.linalg.inv(s0_inv + design.T @ design / sigma2)
    mn = sn @ (s0_inv @ m0 + design.T @ r / sigma2)
    offset_mean, drift_mean = float(mn[0]), float(mn[1])
    offset_std, drift_std = float(np.sqrt(sn[0, 0])), float(np.sqrt(sn[1, 1]))

    corrected = r - (offset_mean + drift_mean * t)
    rmse_residual = float(np.sqrt(np.mean(r**2)))
    corrected_rmse = float(np.sqrt(np.mean(corrected**2)))

    return {
        "buoy_id": buoy_id,
        "sensor_type": sensor_type,
        "n_observations": int(n),
        "posterior": {
            "offset": {"mean": offset_mean, "std": offset_std},
            "drift": {"mean": drift_mean, "std": drift_std},
        },
        "credible_interval_95": {
            "offset": [offset_mean - Z95 * offset_std, offset_mean + Z95 * offset_std],
            "drift": [drift_mean - Z95 * drift_std, drift_mean + Z95 * drift_std],
        },
        "calibration": {"rmse_residual": rmse_residual, "corrected_rmse": corrected_rmse},
    }
