"""Independent reference computations for the sediment verifier.

Recomputes ground truth directly from /app/experiments.db and the live API (joining
the timestamps + levels streams on `seq`); never trusts the agent's output files.
Not available to the agent at solve time.
"""
import json
import sqlite3
import urllib.request

import numpy as np
from scipy.optimize import curve_fit

DB_PATH = "/app/experiments.db"
API_BASE = "http://127.0.0.1:8000"
OUT_DIR = "/app/output"
TARGET_ID = 7
G = 9.81
MIN_SIDE = 5

META_KEYS = [
    "experiment_id", "label", "column_height_cm", "fluid_viscosity_pa_s",
    "fluid_density_kg_m3", "particle_density_kg_m3", "temperature_c",
    "raw_scale", "raw_offset",
]


def metadata(experiment_id=TARGET_ID):
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT e.experiment_id, e.label, e.column_height_cm, e.fluid_viscosity_pa_s, "
        "e.fluid_density_kg_m3, e.particle_density_kg_m3, e.temperature_c, "
        "s.raw_scale, s.raw_offset "
        "FROM experiments e JOIN sensors s ON e.sensor_id = s.sensor_id "
        "WHERE e.experiment_id = ?",
        (experiment_id,),
    ).fetchone()
    con.close()
    return dict(zip(META_KEYS, row))


def _fetch_all(experiment_id, endpoint, key):
    out = {}
    page = 1
    while True:
        with urllib.request.urlopen(
            f"{API_BASE}/experiments/{experiment_id}/{endpoint}?page={page}", timeout=30
        ) as resp:
            payload = json.load(resp)
        for item in payload[key]:
            out[item["seq"]] = item
        if payload["next"] is None:
            break
        page = payload["next"]
    return out


def converted_observations(experiment_id=TARGET_ID):
    meta = metadata(experiment_id)
    ts = _fetch_all(experiment_id, "timestamps", "timestamps")
    lv = _fetch_all(experiment_id, "levels", "levels")
    rows = sorted(
        (ts[seq]["t_ms"] / 1000.0, lv[seq]["raw_level"] * meta["raw_scale"] + meta["raw_offset"])
        for seq in ts if seq in lv
    )
    return rows, len(ts)


def reference_fit(experiment_id=TARGET_ID):
    meta = metadata(experiment_id)
    obs, _ = converted_observations(experiment_id)
    t = np.array([o[0] for o in obs])
    h = np.array([o[1] for o in obs])
    h0 = meta["column_height_cm"]

    candidates = [tc for tc in np.unique(t)
                  if (t < tc).sum() >= MIN_SIDE and (t >= tc).sum() >= MIN_SIDE]
    best = None
    for tc in candidates:
        def model(tt, v1, h_inf, k, _tc=tc):
            hc = h0 - v1 * _tc
            return np.where(tt <= _tc, h0 - v1 * tt,
                            h_inf + (hc - h_inf) * np.exp(-k * np.maximum(tt - _tc, 0.0)))
        try:
            popt, pcov = curve_fit(model, t, h, p0=[1.0, float(h.min()), 0.05], maxfev=10000)
        except Exception:
            continue
        sse = float(np.sum((h - model(t, *popt)) ** 2))
        if best is None or sse < best["sse"]:
            best = {"tc": float(tc), "popt": popt, "pcov": pcov, "sse": sse, "model": model}

    v1, h_inf, k = (float(best["popt"][0]), float(best["popt"][1]), float(best["popt"][2]))
    ci = 1.96 * np.sqrt(np.diag(best["pcov"]))
    pred = best["model"](t, *best["popt"])
    resid = h - pred
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum((h - h.mean()) ** 2))
    d_um = float(np.sqrt(
        18 * meta["fluid_viscosity_pa_s"] * (v1 / 100.0)
        / (G * (meta["particle_density_kg_m3"] - meta["fluid_density_kg_m3"]))
    ) * 1e6)
    return {
        "t_c_s": best["tc"], "v1_cm_per_s": v1, "h_inf_cm": h_inf, "k_per_s": k,
        "v1_cm_per_s_ci95": float(ci[0]), "h_inf_cm_ci95": float(ci[1]), "k_per_s_ci95": float(ci[2]),
        "effective_diameter_um": d_um, "rmse_cm": rmse, "r2": r2, "n_obs": int(len(t)),
    }
