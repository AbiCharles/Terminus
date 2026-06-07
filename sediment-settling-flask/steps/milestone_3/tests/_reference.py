"""Independent reference computations for the sediment verifier.

Holds the correct analysis-method configuration (the answer key for the values an
operator must extract from /app/settling_standard.md), queries /app/experiments.db
for the per-experiment fields, and recomputes ground truth from the live API. It
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

# Correct Revision-C analysis method (governing values from settling_standard.md §8/§9).
CORRECT_METHOD = {
    "settling_model": "two_phase",
    "breakpoint_min_side": 5,
    "p0_v1_cm_per_s": 1.0,
    "p0_k_per_s": 0.05,
    "ci_z_multiplier": 1.96,
    "gravity_m_per_s2": 9.81,
    "time_ms_to_s_divisor": 1000,
    "curve_fit_maxfev": 10000,
    "diameter_output_unit": "micrometre",
}

# Superseded / example / appendix values that must NOT appear in the extracted method.
DISTRACTOR_METHOD = {
    "settling_model": "single_exponential",
    "breakpoint_min_side": 3,
    "p0_v1_cm_per_s": 0.5,
    "p0_k_per_s": 0.10,
    "ci_z_multiplier": 2.0,
    "gravity_m_per_s2": 9.80665,
    "time_ms_to_s_divisor": 60000,
    "curve_fit_maxfev": 5000,
}

EXP_KEYS = ["label", "column_height_cm", "fluid_viscosity_pa_s", "fluid_density_kg_m3",
            "particle_density_kg_m3", "temperature_c", "raw_scale", "raw_offset"]


def experiment(experiment_id=TARGET_ID):
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT e.label, e.column_height_cm, e.fluid_viscosity_pa_s, e.fluid_density_kg_m3, "
        "e.particle_density_kg_m3, e.temperature_c, s.raw_scale, s.raw_offset "
        "FROM experiments e JOIN sensors s ON e.sensor_id = s.sensor_id "
        "WHERE e.experiment_id = ?",
        (experiment_id,),
    ).fetchone()
    con.close()
    return dict(zip(EXP_KEYS, row))


def reference_config(experiment_id=TARGET_ID):
    return {"experiment_id": experiment_id, "experiment": experiment(experiment_id),
            "method": dict(CORRECT_METHOD)}


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
    exp = experiment(experiment_id)
    divisor = CORRECT_METHOD["time_ms_to_s_divisor"]
    ts = _fetch_all(experiment_id, "timestamps", "timestamps")
    lv = _fetch_all(experiment_id, "levels", "levels")
    rows = sorted(
        (ts[seq]["t_ms"] / divisor, lv[seq]["raw_level"] * exp["raw_scale"] + exp["raw_offset"])
        for seq in ts if seq in lv
    )
    return rows, len(ts)


def reference_fit(experiment_id=TARGET_ID):
    exp = experiment(experiment_id)
    obs, _ = converted_observations(experiment_id)
    t = np.array([o[0] for o in obs])
    h = np.array([o[1] for o in obs])
    h0 = exp["column_height_cm"]
    m = CORRECT_METHOD

    candidates = [tc for tc in np.unique(t)
                  if (t < tc).sum() >= m["breakpoint_min_side"]
                  and (t >= tc).sum() >= m["breakpoint_min_side"]]
    best = None
    for tc in candidates:
        def model(tt, v1, h_inf, k, _tc=tc):
            hc = h0 - v1 * _tc
            return np.where(tt <= _tc, h0 - v1 * tt,
                            h_inf + (hc - h_inf) * np.exp(-k * np.maximum(tt - _tc, 0.0)))
        try:
            popt, pcov = curve_fit(model, t, h,
                                   p0=[m["p0_v1_cm_per_s"], float(h.min()), m["p0_k_per_s"]],
                                   maxfev=m["curve_fit_maxfev"])
        except Exception:
            continue
        sse = float(np.sum((h - model(t, *popt)) ** 2))
        if best is None or sse < best["sse"]:
            best = {"tc": float(tc), "popt": popt, "pcov": pcov, "sse": sse, "model": model}

    v1, h_inf, k = (float(best["popt"][0]), float(best["popt"][1]), float(best["popt"][2]))
    ci = m["ci_z_multiplier"] * np.sqrt(np.diag(best["pcov"]))
    resid = h - best["model"](t, *best["popt"])
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum((h - h.mean()) ** 2))
    d_um = float(np.sqrt(18 * exp["fluid_viscosity_pa_s"] * (v1 / 100.0)
                         / (m["gravity_m_per_s2"]
                            * (exp["particle_density_kg_m3"] - exp["fluid_density_kg_m3"]))) * 1e6)
    return {
        "t_c_s": best["tc"], "v1_cm_per_s": v1, "h_inf_cm": h_inf, "k_per_s": k,
        "v1_cm_per_s_ci95": float(ci[0]), "h_inf_cm_ci95": float(ci[1]), "k_per_s_ci95": float(ci[2]),
        "effective_diameter_um": d_um, "rmse_cm": rmse, "r2": r2, "n_obs": int(len(t)),
    }
