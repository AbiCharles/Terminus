"""Generate the sediment-settling fixtures.

Outputs:
  experiments.db (SQLite)  -- agent INPUT: experiments + sensor calibration (no answers)
  observations.db (SQLite) -- the API's private store of RAW sensor readings

Settling model (interface height vs time):
  H(t) = H_inf + (H0 - H_inf) * exp(-k * t)        t in seconds, H in cm, H0 = column height
Raw sensor encoding stored/served by the API:
  raw_level = (H - raw_offset) / raw_scale ;  t_ms = round(t * 1000)
Some observations are flagged invalid (valid=0) and must be filtered before fitting.
"""

import sqlite3

import numpy as np

RNG = np.random.default_rng(20240521)

# 5 experiments; experiment 1 is the task target, the rest are distractors.
EXPERIMENTS = [
    # id, label, H0(cm), mu(Pa·s), rho_f(kg/m3), rho_p(kg/m3), temp_C, sensor_id, H_inf, k
    (1, "col-A-run1", 42.0, 0.0012, 1000.0, 2650.0, 20.0, 10, 8.5, 0.0140),
    (2, "col-A-run2", 42.0, 0.0012, 1000.0, 2650.0, 20.0, 10, 9.2, 0.0125),
    (3, "col-B-run1", 38.0, 0.0015, 1010.0, 2600.0, 25.0, 11, 7.1, 0.0160),
    (4, "col-B-run2", 38.0, 0.0015, 1010.0, 2600.0, 25.0, 11, 6.8, 0.0175),
    (5, "col-C-run1", 50.0, 0.0010, 998.0, 2700.0, 18.0, 12, 11.0, 0.0110),
]
SENSORS = [
    # sensor_id, raw_scale, raw_offset, units
    (10, 0.025, 2.0, "raw_counts"),
    (11, 0.020, 1.5, "raw_counts"),
    (12, 0.030, 3.0, "raw_counts"),
]
N_OBS = 60
T_MAX_S = 360


def model(t, h_inf, k, h0):
    return h_inf + (h0 - h_inf) * np.exp(-k * t)


def build():
    exp_db = sqlite3.connect("experiments.db")
    exp_db.execute("DROP TABLE IF EXISTS experiments")
    exp_db.execute("DROP TABLE IF EXISTS sensors")
    exp_db.execute(
        """CREATE TABLE experiments (
            experiment_id INTEGER PRIMARY KEY, label TEXT, column_height_cm REAL,
            fluid_viscosity_pa_s REAL, fluid_density_kg_m3 REAL, particle_density_kg_m3 REAL,
            temperature_c REAL, sensor_id INTEGER)"""
    )
    exp_db.execute("CREATE TABLE sensors (sensor_id INTEGER PRIMARY KEY, raw_scale REAL, raw_offset REAL, units TEXT)")
    exp_db.executemany("INSERT INTO experiments VALUES (?,?,?,?,?,?,?,?)", [e[:8] for e in EXPERIMENTS])
    exp_db.executemany("INSERT INTO sensors VALUES (?,?,?,?)", SENSORS)
    exp_db.commit()
    exp_db.close()

    obs_db = sqlite3.connect("observations.db")
    obs_db.execute("DROP TABLE IF EXISTS observations")
    obs_db.execute(
        """CREATE TABLE observations (
            experiment_id INTEGER, seq INTEGER, t_ms INTEGER, raw_level REAL, valid INTEGER)"""
    )
    sensor_cal = {s[0]: (s[1], s[2]) for s in SENSORS}
    n_invalid_total = 0
    for exp in EXPERIMENTS:
        eid, _, h0, _, _, _, _, sid, h_inf, k = exp
        scale, offset = sensor_cal[sid]
        t = np.linspace(0, T_MAX_S, N_OBS)
        h = model(t, h_inf, k, h0) + RNG.normal(0, 0.05, N_OBS)
        raw = (h - offset) / scale
        valid = np.ones(N_OBS, dtype=int)
        # inject ~6 invalid readings (sensor dropouts) that must be filtered out
        bad = RNG.choice(N_OBS, size=6, replace=False)
        valid[bad] = 0
        raw[bad] = RNG.choice([-1.0, 0.0, 99999.0], size=6)  # nonsense values
        n_invalid_total += 6
        rows = [(int(eid), int(i), int(round(t[i] * 1000)), float(raw[i]), int(valid[i])) for i in range(N_OBS)]
        obs_db.executemany("INSERT INTO observations VALUES (?,?,?,?,?)", rows)
    obs_db.commit()
    obs_db.close()
    return n_invalid_total


if __name__ == "__main__":
    n_inv = build()
    print(f"experiments={len(EXPERIMENTS)} sensors={len(SENSORS)} obs_per_exp={N_OBS} invalid_injected={n_inv}")
