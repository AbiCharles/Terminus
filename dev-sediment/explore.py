"""Canonical metadata->observations->fit pipeline; confirm well-posed + deterministic."""
import os
import sqlite3

import numpy as np
from scipy.optimize import curve_fit

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_ID = 7
G = 9.81


def metadata(eid):
    con = sqlite3.connect(os.path.join(HERE, "experiments.db"))
    row = con.execute(
        "SELECT e.experiment_id, e.label, e.column_height_cm, e.fluid_viscosity_pa_s, "
        "e.fluid_density_kg_m3, e.particle_density_kg_m3, e.temperature_c, "
        "s.raw_scale, s.raw_offset FROM experiments e JOIN sensors s ON e.sensor_id=s.sensor_id "
        "WHERE e.experiment_id=?", (eid,)
    ).fetchone()
    con.close()
    keys = ["experiment_id", "label", "column_height_cm", "fluid_viscosity_pa_s",
            "fluid_density_kg_m3", "particle_density_kg_m3", "temperature_c",
            "raw_scale", "raw_offset"]
    return dict(zip(keys, row))


def observations(eid, scale, offset):
    con = sqlite3.connect(os.path.join(HERE, "observations.db"))
    rows = con.execute(
        "SELECT t_ms, raw_level FROM observations WHERE experiment_id=? ORDER BY seq", (eid,)
    ).fetchall()
    con.close()
    t_s = np.array([r[0] / 1000.0 for r in rows])
    h_cm = np.array([r[1] * scale + offset for r in rows])
    return t_s, h_cm


def fit(meta, t_s, h_cm):
    h0 = meta["column_height_cm"]

    def model(t, h_inf, k):
        return h_inf + (h0 - h_inf) * np.exp(-k * t)

    p0 = [float(h_cm.min()), 0.05]
    popt, pcov = curve_fit(model, t_s, h_cm, p0=p0, maxfev=10000)
    h_inf, k = float(popt[0]), float(popt[1])
    ci = 1.96 * np.sqrt(np.diag(pcov))
    pred = model(t_s, *popt)
    resid = h_cm - pred
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((h_cm - h_cm.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    v0_cm_s = k * (h0 - h_inf)
    d_um = float(np.sqrt(18 * meta["fluid_viscosity_pa_s"] * (v0_cm_s / 100.0) /
                         (G * (meta["particle_density_kg_m3"] - meta["fluid_density_kg_m3"]))) * 1e6)
    return {
        "h_inf_cm": h_inf, "k_per_s": k,
        "h_inf_ci95": float(ci[0]), "k_ci95": float(ci[1]),
        "v0_cm_per_s": float(v0_cm_s), "effective_diameter_um": d_um,
        "rmse_cm": rmse, "r2": r2, "n_obs": int(len(t_s)),
    }


if __name__ == "__main__":
    m = metadata(TARGET_ID)
    t_s, h_cm = observations(TARGET_ID, m["raw_scale"], m["raw_offset"])
    res = fit(m, t_s, h_cm)
    print("metadata:", {k: m[k] for k in ("experiment_id", "label", "column_height_cm", "raw_scale", "raw_offset")})
    print("n_obs:", len(t_s), "height range:", round(h_cm.min(), 2), "-", round(h_cm.max(), 2))
    print("fit:", {k: round(v, 5) for k, v in res.items()})
    print("(true h_inf=9.5, k=0.045)")
