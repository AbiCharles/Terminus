"""Two-endpoint join + two-phase grid-search fit; confirm well-posed + deterministic."""
import os
import sqlite3

import numpy as np
from scipy.optimize import curve_fit

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_ID = 7
G = 9.81
MIN_SIDE = 5  # min points required on each side of a candidate breakpoint


def metadata(eid):
    con = sqlite3.connect(os.path.join(HERE, "experiments.db"))
    row = con.execute(
        "SELECT e.column_height_cm, e.fluid_viscosity_pa_s, e.fluid_density_kg_m3, "
        "e.particle_density_kg_m3, s.raw_scale, s.raw_offset "
        "FROM experiments e JOIN sensors s ON e.sensor_id=s.sensor_id WHERE e.experiment_id=?",
        (eid,)).fetchone()
    con.close()
    keys = ["column_height_cm", "fluid_viscosity_pa_s", "fluid_density_kg_m3",
            "particle_density_kg_m3", "raw_scale", "raw_offset"]
    return dict(zip(keys, row))


def joined_observations(eid, scale, offset):
    con = sqlite3.connect(os.path.join(HERE, "observations.db"))
    ts = dict(con.execute("SELECT seq, t_ms FROM timestamps WHERE experiment_id=?", (eid,)).fetchall())
    lv = dict(con.execute("SELECT seq, raw_level FROM levels WHERE experiment_id=?", (eid,)).fetchall())
    con.close()
    rows = sorted((ts[seq] / 1000.0, lv[seq] * scale + offset) for seq in ts if seq in lv)
    return np.array([r[0] for r in rows]), np.array([r[1] for r in rows])


def fit_two_phase(meta, t, h):
    h0 = meta["column_height_cm"]
    uniq = np.unique(t)
    candidates = [tc for tc in uniq if (t < tc).sum() >= MIN_SIDE and (t >= tc).sum() >= MIN_SIDE]
    best = None
    for tc in candidates:
        def model(tt, v1, h_inf, k, _tc=tc):
            hc = h0 - v1 * _tc
            return np.where(tt <= _tc, h0 - v1 * tt, h_inf + (hc - h_inf) * np.exp(-k * (tt - _tc)))
        try:
            popt, pcov = curve_fit(model, t, h, p0=[1.0, float(h.min()), 0.05], maxfev=10000)
        except Exception:
            continue
        sse = float(np.sum((h - model(t, *popt)) ** 2))
        if best is None or sse < best["sse"]:
            best = dict(tc=float(tc), popt=popt, pcov=pcov, sse=sse, model=model)
    popt, pcov = best["popt"], best["pcov"]
    v1, h_inf, k = (float(popt[0]), float(popt[1]), float(popt[2]))
    ci = 1.96 * np.sqrt(np.diag(pcov))
    pred = best["model"](t, *popt)
    resid = h - pred
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum((h - h.mean()) ** 2))
    d_um = float(np.sqrt(18 * meta["fluid_viscosity_pa_s"] * (v1 / 100.0) /
                         (G * (meta["particle_density_kg_m3"] - meta["fluid_density_kg_m3"]))) * 1e6)
    return {
        "breakpoint_t_c_s": best["tc"], "v1_cm_per_s": v1, "h_inf_cm": h_inf, "k_per_s": k,
        "v1_ci95": float(ci[0]), "h_inf_ci95": float(ci[1]), "k_ci95": float(ci[2]),
        "effective_diameter_um": d_um, "rmse_cm": rmse, "r2": r2, "n_obs": int(len(t)),
    }


if __name__ == "__main__":
    m = metadata(TARGET_ID)
    t, h = joined_observations(TARGET_ID, m["raw_scale"], m["raw_offset"])
    res = fit_two_phase(m, t, h)
    print("n_obs:", len(t), "height range:", round(h.min(), 2), "-", round(h.max(), 2))
    print("fit:", {k: round(v, 5) for k, v in res.items()})
    print("(true t_c=12, v1=1.8, h_inf=9.5, k=0.08)")
