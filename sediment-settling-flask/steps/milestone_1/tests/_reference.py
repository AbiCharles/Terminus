"""Independent reference for the sediment-settling pipeline.

Recomputes ground truth from the raw inputs alone: the SQLite metadata DB and the
RAW observations served by the Flask API (fetched here, paginated, then converted,
filtered and refit). It does NOT trust the agent's /app/output files — it is the
verifier's answer key. The agent has no access to this module at solve time.
"""

import json
import sqlite3
import urllib.request

import numpy as np
from scipy.optimize import curve_fit

DB_PATH = "/app/experiments.db"
API = "http://127.0.0.1:8000"
EXPERIMENT_ID = 1
G = 9.81
META_KEYS = ["experiment_id", "label", "column_height_cm", "fluid_viscosity_pa_s",
             "fluid_density_kg_m3", "particle_density_kg_m3", "temperature_c",
             "sensor_id", "raw_scale", "raw_offset"]


def get(path):
    return json.load(urllib.request.urlopen(API + path, timeout=5))


def metadata():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    e = con.execute(
        """SELECT e.*, s.raw_scale, s.raw_offset FROM experiments e
           JOIN sensors s ON s.sensor_id = e.sensor_id WHERE e.experiment_id = ?""",
        (EXPERIMENT_ID,)).fetchone()
    con.close()
    return {k: e[k] for k in META_KEYS}


def observations(md=None):
    """Return sorted list of (time_s, height_cm) for valid observations, fetched from the API."""
    if md is None:
        md = metadata()
    first = get(f"/experiments/{EXPERIMENT_ID}/observations?page=1")
    obs = list(first["observations"])
    for pg in range(2, first["total_pages"] + 1):
        obs += get(f"/experiments/{EXPERIMENT_ID}/observations?page={pg}")["observations"]
    rows = sorted(
        (o["t_ms"] / 1000.0, o["raw_level"] * md["raw_scale"] + md["raw_offset"])
        for o in obs if o["valid"] == 1
    )
    return rows


def _model(t, h_inf, k, h0):
    return h_inf + (h0 - h_inf) * np.exp(-k * t)


def fit():
    md = metadata()
    h0 = md["column_height_cm"]
    rows = observations(md)
    t = np.array([r[0] for r in rows])
    h = np.array([r[1] for r in rows])
    popt, pcov = curve_fit(lambda tt, hi, k: _model(tt, hi, k, h0), t, h,
                           p0=[h0 / 2.0, 0.01], maxfev=10000)
    h_inf, k = popt
    ci = 1.96 * np.sqrt(np.diag(pcov))
    v0 = k * (h0 - h_inf)
    d_um = np.sqrt(18.0 * md["fluid_viscosity_pa_s"] * (v0 / 100.0)
                   / (G * (md["particle_density_kg_m3"] - md["fluid_density_kg_m3"]))) * 1e6
    resid = h - _model(t, h_inf, k, h0)
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum((h - h.mean()) ** 2))
    return {
        "experiment_id": EXPERIMENT_ID, "h_inf_cm": float(h_inf), "k_per_s": float(k),
        "h_inf_ci95": float(ci[0]), "k_ci95": float(ci[1]),
        "initial_velocity_cm_s": float(v0), "effective_diameter_um": float(d_um),
        "rmse": rmse, "r2": r2, "n_obs": int(len(t)),
    }
