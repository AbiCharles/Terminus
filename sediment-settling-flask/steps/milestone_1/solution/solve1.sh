#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the full sediment_cli.py and run its `config`
# subcommand. `config` extracts the analysis-method configuration from the
# governing sections of /app/settling_standard.md (skipping the superseded /
# example / appendix distractors) and the per-experiment metadata + calibration
# from /app/experiments.db, writing /app/output/config.json for experiment 7.
cat > /app/sediment_cli.py <<'PY'
"""Sediment settling-column inference CLI (standard-driven)."""
import argparse
import csv
import json
import os
import re
import sqlite3

import numpy as np
import pandas as pd
import requests
from scipy.optimize import curve_fit

DB_PATH = "/app/experiments.db"
STANDARD_PATH = "/app/settling_standard.md"
API_BASE = "http://127.0.0.1:8000"
OUT_DIR = "/app/output"
CONFIG_PATH = "/app/output/config.json"

EXP_KEYS = ["label", "column_height_cm", "fluid_viscosity_pa_s", "fluid_density_kg_m3",
            "particle_density_kg_m3", "temperature_c", "raw_scale", "raw_offset"]


def get_experiment(experiment_id):
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


def parse_method():
    raw = open(STANDARD_PATH, encoding="utf-8").read()
    # restrict to the governing units/method sections (skip example, history, appendices)
    text = raw[raw.index("## §8"):raw.index("## §10")].replace("**", "")

    def find(pattern, cast=str):
        m = re.search(pattern, text)
        if not m:
            raise SystemExit(f"method extraction failed: {pattern}")
        return cast(m.group(1))

    return {
        "settling_model": "two_phase" if re.search(r"Use the two-phase model", text) else None,
        "breakpoint_min_side": find(r"at\s+least\s+(\d+)\s+observations\s+on\s+each\s+side", int),
        "p0_v1_cm_per_s": find(r"v1\s*=\s*([0-9.]+)\s*cm/s", float),
        "p0_k_per_s": find(r"k\s*=\s*([0-9.]+)\s*1/s", float),
        "ci_z_multiplier": find(r"multiplier\s+at\s+([0-9.]+)", float),
        "gravity_m_per_s2": find(r"g\s*=\s*([0-9.]+)\s*m/s", float),
        "time_ms_to_s_divisor": find(r"dividing\s+by\s+(\d+)", int),
        "curve_fit_maxfev": find(r"maximum\s+of\s+(\d+)\s+function\s+evaluations", int),
        "diameter_output_unit": "micrometre" if re.search(r"expressed\s+in\s+micrometres", text) else None,
    }


def load_config():
    with open(CONFIG_PATH) as fh:
        return json.load(fh)


def cmd_config(experiment_id):
    config = {
        "experiment_id": experiment_id,
        "experiment": get_experiment(experiment_id),
        "method": parse_method(),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as fh:
        json.dump(config, fh, indent=2)


def _fetch_all(experiment_id, endpoint, key):
    out = {}
    page = 1
    while True:
        resp = requests.get(f"{API_BASE}/experiments/{experiment_id}/{endpoint}",
                            params={"page": page}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        for item in payload[key]:
            out[item["seq"]] = item
        if payload["next"] is None:
            break
        page = payload["next"]
    return out


def cmd_observations(experiment_id):
    config = load_config()
    exp = config["experiment"]
    divisor = config["method"]["time_ms_to_s_divisor"]
    ts = _fetch_all(experiment_id, "timestamps", "timestamps")
    lv = _fetch_all(experiment_id, "levels", "levels")
    rows = sorted(
        (ts[seq]["t_ms"] / divisor, lv[seq]["raw_level"] * exp["raw_scale"] + exp["raw_offset"])
        for seq in ts if seq in lv
    )
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "observations.csv"), "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["time_s", "height_cm"])
        writer.writerows(rows)


def _two_phase_fit(t, h, h0, method):
    candidates = [tc for tc in np.unique(t)
                  if (t < tc).sum() >= method["breakpoint_min_side"]
                  and (t >= tc).sum() >= method["breakpoint_min_side"]]
    best = None
    for tc in candidates:
        def model(tt, v1, h_inf, k, _tc=tc):
            hc = h0 - v1 * _tc
            return np.where(tt <= _tc, h0 - v1 * tt,
                            h_inf + (hc - h_inf) * np.exp(-k * np.maximum(tt - _tc, 0.0)))
        try:
            popt, pcov = curve_fit(
                model, t, h,
                p0=[method["p0_v1_cm_per_s"], float(h.min()), method["p0_k_per_s"]],
                maxfev=method["curve_fit_maxfev"],
            )
        except Exception:
            continue
        sse = float(np.sum((h - model(t, *popt)) ** 2))
        if best is None or sse < best["sse"]:
            best = {"tc": float(tc), "popt": popt, "pcov": pcov, "sse": sse, "model": model}
    return best


def cmd_fit(experiment_id):
    config = load_config()
    exp, method = config["experiment"], config["method"]
    df = pd.read_csv(os.path.join(OUT_DIR, "observations.csv"))
    t, h = df["time_s"].to_numpy(), df["height_cm"].to_numpy()
    best = _two_phase_fit(t, h, exp["column_height_cm"], method)
    v1, h_inf, k = (float(best["popt"][0]), float(best["popt"][1]), float(best["popt"][2]))
    ci = method["ci_z_multiplier"] * np.sqrt(np.diag(best["pcov"]))
    resid = h - best["model"](t, *best["popt"])
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum((h - h.mean()) ** 2))
    d_um = float(np.sqrt(18 * exp["fluid_viscosity_pa_s"] * (v1 / 100.0)
                         / (method["gravity_m_per_s2"]
                            * (exp["particle_density_kg_m3"] - exp["fluid_density_kg_m3"]))) * 1e6)
    report = {
        "experiment_id": experiment_id,
        "breakpoint": {"t_c_s": best["tc"]},
        "parameters": {"v1_cm_per_s": v1, "h_inf_cm": h_inf, "k_per_s": k},
        "ci95": {"v1_cm_per_s": float(ci[0]), "h_inf_cm": float(ci[1]), "k_per_s": float(ci[2])},
        "derived": {"effective_diameter_um": d_um},
        "residuals": {"rmse_cm": rmse, "r2": r2, "n_obs": int(len(t))},
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "report.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    table = [
        ("t_c_s", best["tc"]), ("v1_cm_per_s", v1), ("h_inf_cm", h_inf), ("k_per_s", k),
        ("v1_cm_per_s_ci95", float(ci[0])), ("h_inf_cm_ci95", float(ci[1])),
        ("k_per_s_ci95", float(ci[2])), ("effective_diameter_um", d_um),
        ("rmse_cm", rmse), ("r2", r2), ("n_obs", int(len(t))),
    ]
    with open(os.path.join(OUT_DIR, "report.csv"), "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["quantity", "value"])
        writer.writerows(table)


def main():
    parser = argparse.ArgumentParser(description="Sediment settling-column inference")
    parser.add_argument("command", choices=["config", "observations", "fit"])
    parser.add_argument("--experiment-id", type=int, required=True)
    args = parser.parse_args()
    {"config": cmd_config, "observations": cmd_observations, "fit": cmd_fit}[args.command](
        args.experiment_id
    )


if __name__ == "__main__":
    main()
PY

python3 /app/sediment_cli.py config --experiment-id 7
