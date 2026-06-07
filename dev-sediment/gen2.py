"""Deepened dataset: TWO-PHASE settling (free settling -> compression with an
unknown breakpoint), served via two separate paginated endpoints (timestamps and
levels) that must be joined by `seq`. Levels are stored shuffled so a positional
zip fails; you must join on seq.
"""
import os
import sqlite3

import numpy as np

RNG = np.random.default_rng(13127)
TARGET_ID = 7
N_EXP = 12

TARGET = dict(
    column_height_cm=42.0, v1=1.80, t_c=12.0, h_inf=9.5, k=0.080,
    viscosity=0.00102, fluid_density=998.0, particle_density=2600.0, temperature=21.0,
    raw_scale=0.011, raw_offset=0.5, n_obs=61, noise_cm=0.15,
)


def two_phase(t, h0, v1, t_c, h_inf, k):
    hc = h0 - v1 * t_c
    return np.where(t <= t_c, h0 - v1 * t, h_inf + (hc - h_inf) * np.exp(-k * (t - t_c)))


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
        CREATE TABLE sensors (sensor_id INTEGER PRIMARY KEY, model TEXT, units TEXT,
                              raw_scale REAL, raw_offset REAL);
        CREATE TABLE experiments (experiment_id INTEGER PRIMARY KEY, label TEXT,
                              column_height_cm REAL, fluid_viscosity_pa_s REAL,
                              fluid_density_kg_m3 REAL, particle_density_kg_m3 REAL,
                              temperature_c REAL, sensor_id INTEGER);
        """
    )
    obs = sqlite3.connect(obs_path)
    # store both streams; `levels` get an independent shuffled order index
    obs.execute("CREATE TABLE timestamps (experiment_id INTEGER, seq INTEGER, t_ms INTEGER, ord_idx INTEGER)")
    obs.execute("CREATE TABLE levels (experiment_id INTEGER, seq INTEGER, raw_level INTEGER, ord_idx INTEGER)")

    for eid in range(1, N_EXP + 1):
        if eid == TARGET_ID:
            p = TARGET
        else:
            p = dict(
                column_height_cm=float(np.round(RNG.uniform(30, 50), 1)),
                v1=float(np.round(RNG.uniform(1.0, 2.5), 3)),
                t_c=float(np.round(RNG.uniform(8, 18), 1)),
                h_inf=float(np.round(RNG.uniform(6, 14), 2)),
                k=float(np.round(RNG.uniform(0.05, 0.12), 4)),
                viscosity=float(np.round(RNG.uniform(0.0009, 0.0014), 6)),
                fluid_density=float(np.round(RNG.uniform(995, 1005), 1)),
                particle_density=float(np.round(RNG.uniform(2300, 2700), 1)),
                temperature=float(np.round(RNG.uniform(18, 24), 1)),
                raw_scale=float(np.round(RNG.uniform(0.009, 0.013), 5)),
                raw_offset=float(np.round(RNG.uniform(0.0, 1.0), 3)),
                n_obs=int(RNG.integers(55, 75)), noise_cm=0.15,
            )
        exp.execute("INSERT INTO sensors VALUES (?,?,?,?,?)",
                    (eid, f"ColumnProbe-{eid:02d}", "cm", p["raw_scale"], p["raw_offset"]))
        exp.execute("INSERT INTO experiments VALUES (?,?,?,?,?,?,?,?)",
                    (eid, f"SC-22{eid:02d}", p["column_height_cm"], p["viscosity"],
                     p["fluid_density"], p["particle_density"], p["temperature"], eid))

        t_s = np.arange(p["n_obs"], dtype=float)
        h = two_phase(t_s, p["column_height_cm"], p["v1"], p["t_c"], p["h_inf"], p["k"])
        h_noisy = h + RNG.normal(0, p["noise_cm"], size=h.shape)
        raw = np.rint((h_noisy - p["raw_offset"]) / p["raw_scale"]).astype(int)
        t_ms = (t_s * 1000).astype(int)
        n = p["n_obs"]
        # timestamps stored in seq order; levels stored in a shuffled order
        level_order = RNG.permutation(n)
        for seq in range(n):
            obs.execute("INSERT INTO timestamps VALUES (?,?,?,?)", (eid, seq, int(t_ms[seq]), seq))
        for ord_idx, seq in enumerate(level_order):
            obs.execute("INSERT INTO levels VALUES (?,?,?,?)", (eid, int(seq), int(raw[seq]), ord_idx))

    exp.commit(); exp.close()
    obs.commit(); obs.close()
    return exp_path, obs_path


if __name__ == "__main__":
    e, o = build()
    print("wrote", os.path.basename(e), os.path.basename(o),
          f"({os.path.getsize(e)}B, {os.path.getsize(o)}B)")
    print(f"  TARGET {TARGET_ID}: H0={TARGET['column_height_cm']} v1={TARGET['v1']} t_c={TARGET['t_c']} h_inf={TARGET['h_inf']} k={TARGET['k']}")
