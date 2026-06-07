"""Reference sediment fit for experiment 1 — used to lock numbers + tolerances."""

import sqlite3

import numpy as np
from scipy.optimize import curve_fit

G = 9.81
EXPERIMENT_ID = 1
P0 = None  # set from H0 below
MAXFEV = 10000


def model(t, h_inf, k, h0):
    return h_inf + (h0 - h_inf) * np.exp(-k * t)


def load_metadata(eid):
    con = sqlite3.connect("experiments.db")
    con.row_factory = sqlite3.Row
    e = con.execute(
        """SELECT e.*, s.raw_scale, s.raw_offset
           FROM experiments e JOIN sensors s ON s.sensor_id = e.sensor_id
           WHERE e.experiment_id = ?""", (eid,)).fetchone()
    con.close()
    return dict(e)


def load_observations(eid, scale, offset):
    con = sqlite3.connect("observations.db")
    rows = con.execute(
        "SELECT t_ms, raw_level, valid FROM observations WHERE experiment_id = ? ORDER BY t_ms",
        (eid,)).fetchall()
    con.close()
    t, h = [], []
    for t_ms, raw, valid in rows:
        if valid != 1:
            continue
        t.append(t_ms / 1000.0)
        h.append(raw * scale + offset)
    return np.array(t), np.array(h)


def main():
    meta = load_metadata(EXPERIMENT_ID)
    h0 = meta["column_height_cm"]
    t, h = load_observations(EXPERIMENT_ID, meta["raw_scale"], meta["raw_offset"])

    popt, pcov = curve_fit(lambda tt, hi, k: model(tt, hi, k, h0), t, h,
                           p0=[h0 / 2.0, 0.01], maxfev=MAXFEV)
    h_inf, k = popt
    perr = np.sqrt(np.diag(pcov))
    ci = 1.96 * perr

    v0 = k * (h0 - h_inf)            # cm/s
    v0_si = v0 / 100.0               # m/s
    mu, rho_p, rho_f = meta["fluid_viscosity_pa_s"], meta["particle_density_kg_m3"], meta["fluid_density_kg_m3"]
    d_m = np.sqrt(18.0 * mu * v0_si / (G * (rho_p - rho_f)))
    d_um = d_m * 1e6

    resid = h - model(t, h_inf, k, h0)
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((h - h.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot

    print(f"n_obs(valid)={len(t)}")
    print(f"H_inf={h_inf:.6f} cm (95% CI ±{ci[0]:.6f})")
    print(f"k={k:.6f} /s (95% CI ±{ci[1]:.6f})")
    print(f"v0={v0:.6f} cm/s | effective_diameter={d_um:.4f} um")
    print(f"rmse={rmse:.6f} r2={r2:.6f}")


if __name__ == "__main__":
    main()
