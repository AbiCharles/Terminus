"""Generate the SQLite databases for the sediment-settling task.

  experiments.db (agent-visible): `experiments` + `sensors` tables — INPUTS ONLY
                 (experiment metadata + calibration constants; no answers).
  observations.db (API-private): `observations` table of RAW sensor readings the
                 Flask API serves over HTTP (t_ms, raw_level), paginated.

Heights follow a compression-settling curve H(t) = H_inf + (H0 - H_inf) e^{-k t};
the API serves raw ADC counts, height_cm = raw_level * raw_scale + raw_offset.
The task targets one experiment (TARGET_ID); others are realistic decoys.
"""
import os
import sqlite3

import numpy as np

RNG = np.random.default_rng(4801)
TARGET_ID = 7
N_EXP = 12

# True settling parameters + physical constants for the TARGET experiment.
TARGET = dict(
    column_height_cm=42.0, h_inf=9.5, k=0.045,
    viscosity=0.00102, fluid_density=998.0, particle_density=2600.0, temperature=21.0,
    raw_scale=0.011, raw_offset=0.5, n_obs=131, noise_cm=0.15,
)


def settle(t_s, h0, h_inf, k):
    return h_inf + (h0 - h_inf) * np.exp(-k * t_s)


def build():
    here = os.path.dirname(os.path.abspath(__file__))
    exp_path = os.path.join(here, "experiments.db")
    obs_path = os.path.join(here, "observations.db")
    for p in (exp_path, obs_path):
        if os.path.exists(p):
            os.remove(p)

    exp = sqlite3.connect(exp_path)
    exp.executescript(
        """
        CREATE TABLE sensors (
            sensor_id INTEGER PRIMARY KEY,
            model TEXT, units TEXT,
            raw_scale REAL, raw_offset REAL
        );
        CREATE TABLE experiments (
            experiment_id INTEGER PRIMARY KEY,
            label TEXT,
            column_height_cm REAL,
            fluid_viscosity_pa_s REAL,
            fluid_density_kg_m3 REAL,
            particle_density_kg_m3 REAL,
            temperature_c REAL,
            sensor_id INTEGER,
            FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id)
        );
        """
    )
    obs = sqlite3.connect(obs_path)
    obs.execute(
        "CREATE TABLE observations (experiment_id INTEGER, seq INTEGER, t_ms INTEGER, raw_level INTEGER)"
    )

    for eid in range(1, N_EXP + 1):
        is_target = eid == TARGET_ID
        if is_target:
            p = TARGET
        else:
            p = dict(
                column_height_cm=float(np.round(RNG.uniform(30, 50), 1)),
                h_inf=float(np.round(RNG.uniform(6, 14), 2)),
                k=float(np.round(RNG.uniform(0.02, 0.08), 4)),
                viscosity=float(np.round(RNG.uniform(0.0009, 0.0014), 6)),
                fluid_density=float(np.round(RNG.uniform(995, 1005), 1)),
                particle_density=float(np.round(RNG.uniform(2300, 2700), 1)),
                temperature=float(np.round(RNG.uniform(18, 24), 1)),
                raw_scale=float(np.round(RNG.uniform(0.009, 0.013), 5)),
                raw_offset=float(np.round(RNG.uniform(0.0, 1.0), 3)),
                n_obs=int(RNG.integers(90, 140)),
                noise_cm=0.15,
            )
        exp.execute(
            "INSERT INTO sensors VALUES (?,?,?,?,?)",
            (eid, f"ColumnProbe-{eid:02d}", "cm", p["raw_scale"], p["raw_offset"]),
        )
        exp.execute(
            "INSERT INTO experiments VALUES (?,?,?,?,?,?,?,?)",
            (eid, f"SC-22{eid:02d}", p["column_height_cm"], p["viscosity"],
             p["fluid_density"], p["particle_density"], p["temperature"], eid),
        )
        t_s = np.arange(p["n_obs"], dtype=float)
        h = settle(t_s, p["column_height_cm"], p["h_inf"], p["k"])
        h_noisy = h + RNG.normal(0, p["noise_cm"], size=h.shape)
        raw = np.rint((h_noisy - p["raw_offset"]) / p["raw_scale"]).astype(int)
        for seq, (tt, rr) in enumerate(zip((t_s * 1000).astype(int), raw)):
            obs.execute(
                "INSERT INTO observations VALUES (?,?,?,?)", (eid, seq, int(tt), int(rr))
            )

    exp.commit(); exp.close()
    obs.commit(); obs.close()
    return exp_path, obs_path


if __name__ == "__main__":
    exp_path, obs_path = build()
    print("wrote", os.path.basename(exp_path), os.path.basename(obs_path))
    print(f"  experiments.db: {os.path.getsize(exp_path)} bytes | observations.db: {os.path.getsize(obs_path)} bytes")
    print(f"  TARGET experiment_id={TARGET_ID}: H0={TARGET['column_height_cm']} h_inf={TARGET['h_inf']} k={TARGET['k']}")
