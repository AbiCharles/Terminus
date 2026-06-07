"""Independent reference computations for the sediment verifier.

Recomputes ground truth directly from /app/experiments.db and the live API; it
never trusts the agent's output files. Not available to the agent at solve time.
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


def _api_get(path):
    with urllib.request.urlopen(API_BASE + path, timeout=30) as resp:
        return json.load(resp)


def raw_observations(experiment_id=TARGET_ID):
    rows = []
    total = None
    page = 1
    while True:
        payload = _api_get(f"/experiments/{experiment_id}/observations?page={page}")
        total = payload["total"]
        rows.extend(payload["observations"])
        if payload["next"] is None:
            break
        page = payload["next"]
    return rows, total


def converted_observations(experiment_id=TARGET_ID):
    meta = metadata(experiment_id)
    raw, total = raw_observations(experiment_id)
    obs = sorted(
        (o["t_ms"] / 1000.0, o["raw_level"] * meta["raw_scale"] + meta["raw_offset"])
        for o in raw
    )
    return obs, total


def reference_fit(experiment_id=TARGET_ID):
    meta = metadata(experiment_id)
    obs, _ = converted_observations(experiment_id)
    t = np.array([o[0] for o in obs])
    h = np.array([o[1] for o in obs])
    h0 = meta["column_height_cm"]

    def model(t, h_inf, k):
        return h_inf + (h0 - h_inf) * np.exp(-k * t)

    popt, pcov = curve_fit(model, t, h, p0=[float(h.min()), 0.05], maxfev=10000)
    h_inf, k = float(popt[0]), float(popt[1])
    ci = 1.96 * np.sqrt(np.diag(pcov))
    pred = model(t, *popt)
    resid = h - pred
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum((h - h.mean()) ** 2))
    v0 = k * (h0 - h_inf)
    d_um = float(np.sqrt(
        18 * meta["fluid_viscosity_pa_s"] * (v0 / 100.0)
        / (G * (meta["particle_density_kg_m3"] - meta["fluid_density_kg_m3"]))
    ) * 1e6)
    return {
        "h_inf_cm": h_inf, "k_per_s": k,
        "h_inf_cm_ci95": float(ci[0]), "k_per_s_ci95": float(ci[1]),
        "v0_cm_per_s": float(v0), "effective_diameter_um": d_um,
        "rmse_cm": rmse, "r2": r2, "n_obs": int(len(t)),
    }
