"""Independent reference implementation for the buoy calibration task.

Encodes the binding calibration protocol (the answer key for milestone 1) and
recomputes, directly from the SQLite store at /app/observations.db, the cleaned
residual series (milestone 2) and the heteroscedastic, three-parameter
change-point Bayesian posterior (milestone 3). It never reads the agent's
protocol.json or /app/artifacts, so an agent cannot weaken verification by
tampering with its own outputs, and the agent has no access to this module.

The model, per buoy, on the cleaned residual r(t) = converted - reference:

    r = offset + drift * t + drift_change * max(0, t - t_changepoint) + noise,
    noise ~ Normal(0, measurement_std**2)   (heteroscedastic, weights = 1/std**2)

with independent per-sensor-type Gaussian priors on (offset, drift, drift_change).
The posterior is the conjugate weighted (generalized least squares) Gaussian.
"""

import sqlite3
from datetime import datetime, timezone

import numpy as np

DB_PATH = "/app/observations.db"

MISSION_EPOCH = "2024-01-01T00:00:00Z"
TIME_UNIT = "days"
ACTIVE_STATUS = "active"
INCLUDED_SENSOR_TYPES = ["pressure", "temperature"]
DRIFT_CHANGEPOINT = "2024-03-17T00:00:00Z"

UNIT_CONVERSION = {"temperature": 0.0625, "pressure": 0.1}
PRIORS = {
    "temperature": {
        "offset": {"mean": 0.0, "std": 0.5},
        "drift": {"mean": 0.0, "std": 0.02},
        "drift_change": {"mean": 0.0, "std": 0.02},
    },
    "pressure": {
        "offset": {"mean": 0.0, "std": 2.0},
        "drift": {"mean": 0.0, "std": 0.05},
        "drift_change": {"mean": 0.0, "std": 0.05},
    },
}
EXCLUSION_INTERVALS = [
    {"buoy_id": "ALL", "start": "2024-03-10T00:00:00Z", "end": "2024-03-17T00:00:00Z"},
    {"buoy_id": "B003", "start": "2024-05-01T00:00:00Z", "end": "2024-05-20T00:00:00Z"},
]

Z95 = 1.959963984540054
PARAMS = ("offset", "drift", "drift_change")


def _parse(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


_EPOCH_DT = _parse(MISSION_EPOCH)
T_CHANGE = (_parse(DRIFT_CHANGEPOINT) - _EPOCH_DT).total_seconds() / 86400.0


def expected_protocol():
    """The binding protocol that milestone 1 must extract into /app/protocol.json."""
    return {
        "mission_epoch": MISSION_EPOCH,
        "time_unit": TIME_UNIT,
        "active_status": ACTIVE_STATUS,
        "included_sensor_types": INCLUDED_SENSOR_TYPES,
        "drift_changepoint": DRIFT_CHANGEPOINT,
        "sensors": {
            "temperature": {"unit_conversion": UNIT_CONVERSION["temperature"], "priors": PRIORS["temperature"]},
            "pressure": {"unit_conversion": UNIT_CONVERSION["pressure"], "priors": PRIORS["pressure"]},
        },
        "exclusion_intervals": EXCLUSION_INTERVALS,
    }


def valid_experiment_ids(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT buoy_id, sensor_type FROM buoys WHERE status = ? ORDER BY buoy_id",
            (ACTIVE_STATUS,),
        ).fetchall()
    finally:
        con.close()
    return [b for b, s in rows if s in INCLUDED_SENSOR_TYPES]


# Back-compat aliases used by the test modules.
def included_buoys(db_path=DB_PATH):
    return valid_experiment_ids(db_path)


def nonvalid_buoys(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    try:
        allids = [r[0] for r in con.execute("SELECT buoy_id FROM buoys").fetchall()]
    finally:
        con.close()
    return sorted(set(allids) - set(valid_experiment_ids(db_path)))


def buoy_sensor_type(buoy_id, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT sensor_type FROM buoys WHERE buoy_id = ?", (buoy_id,)).fetchone()
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
    """Cleaned residual series for a buoy after inclusion, exclusion and conversion."""
    sensor_type = buoy_sensor_type(buoy_id, db_path)
    scale = UNIT_CONVERSION[sensor_type]
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT timestamp, raw_reading, reference_reading, measurement_std FROM observations "
            "WHERE buoy_id = ? ORDER BY timestamp",
            (buoy_id,),
        ).fetchall()
    finally:
        con.close()
    out = {k: [] for k in ("timestamp", "t_days", "converted_value", "reference_value", "residual", "measurement_std", "sensor_type")}
    for ts, raw, ref, std in rows:
        ts_dt = _parse(ts)
        if _is_excluded(buoy_id, ts_dt):
            continue
        converted = raw * scale
        out["timestamp"].append(ts)
        out["t_days"].append((ts_dt - _EPOCH_DT).total_seconds() / 86400.0)
        out["converted_value"].append(converted)
        out["reference_value"].append(ref)
        out["residual"].append(converted - ref)
        out["measurement_std"].append(std)
        out["sensor_type"].append(sensor_type)
    return out


def accepted(buoy_id, db_path=DB_PATH):
    """Acceptance gate (notebook §13): a buoy's calibration is accepted — and its
    model registered — only if its drift_change is statistically resolved, i.e. the
    95% credible interval for drift_change excludes zero."""
    lo, hi = posterior(buoy_id, db_path)["credible_interval_95"]["drift_change"]
    return not (lo <= 0.0 <= hi)


def posterior(buoy_id, db_path=DB_PATH):
    """Heteroscedastic three-parameter change-point conjugate Gaussian posterior."""
    sensor_type = buoy_sensor_type(buoy_id, db_path)
    series = clean_series(buoy_id, db_path)
    t = np.array(series["t_days"], dtype=np.float64)
    r = np.array(series["residual"], dtype=np.float64)
    std = np.array(series["measurement_std"], dtype=np.float64)
    n = t.shape[0]

    hinge = np.maximum(0.0, t - T_CHANGE)
    design = np.column_stack([np.ones(n), t, hinge])
    w = 1.0 / std**2
    atwa = design.T @ (design * w[:, None])
    atwr = design.T @ (r * w)

    priors = PRIORS[sensor_type]
    m0 = np.array([priors[p]["mean"] for p in PARAMS], dtype=np.float64)
    s0_inv = np.diag([1.0 / priors[p]["std"] ** 2 for p in PARAMS])

    sn = np.linalg.inv(s0_inv + atwa)
    mn = sn @ (s0_inv @ m0 + atwr)
    sds = np.sqrt(np.diag(sn))

    fitted = design @ mn
    corrected = r - fitted
    return {
        "buoy_id": buoy_id,
        "sensor_type": sensor_type,
        "n_observations": int(n),
        "changepoint_t_days": float(T_CHANGE),
        "posterior": {p: {"mean": float(mn[i]), "std": float(sds[i])} for i, p in enumerate(PARAMS)},
        "credible_interval_95": {
            p: [float(mn[i] - Z95 * sds[i]), float(mn[i] + Z95 * sds[i])] for i, p in enumerate(PARAMS)
        },
        "calibration": {
            "rmse_residual": float(np.sqrt(np.mean(r**2))),
            "corrected_rmse": float(np.sqrt(np.mean(corrected**2))),
        },
    }
