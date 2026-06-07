#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the analysis CLI and run its `metadata` step. The CLI
# (reused by milestones 2 and 3) joins experiment 1 with its sensor calibration
# from SQLite and writes /app/output/metadata.json (per /app/spec.md §2).
bash /app/start_api.sh

cat > /app/sediment_cli.py <<'PY'
"""Settling-column analysis CLI: metadata | observations | fit (experiment 1)."""
import argparse
import csv
import json
import os
import sqlite3
import urllib.request

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

API = "http://127.0.0.1:8000"
EXPERIMENT_ID = 1
G = 9.81
OUT = "/app/output"
META_KEYS = ["experiment_id", "label", "column_height_cm", "fluid_viscosity_pa_s",
             "fluid_density_kg_m3", "particle_density_kg_m3", "temperature_c",
             "sensor_id", "raw_scale", "raw_offset"]


def _get(path):
    return json.load(urllib.request.urlopen(API + path, timeout=5))


def metadata():
    con = sqlite3.connect("/app/experiments.db")
    con.row_factory = sqlite3.Row
    e = con.execute(
        """SELECT e.*, s.raw_scale, s.raw_offset FROM experiments e
           JOIN sensors s ON s.sensor_id = e.sensor_id WHERE e.experiment_id = ?""",
        (EXPERIMENT_ID,)).fetchone()
    con.close()
    md = {k: e[k] for k in META_KEYS}
    os.makedirs(OUT, exist_ok=True)
    json.dump(md, open(f"{OUT}/metadata.json", "w"), indent=2)
    return md


def observations():
    md = json.load(open(f"{OUT}/metadata.json"))
    first = _get(f"/experiments/{EXPERIMENT_ID}/observations?page=1")
    obs = list(first["observations"])
    for pg in range(2, first["total_pages"] + 1):
        obs += _get(f"/experiments/{EXPERIMENT_ID}/observations?page={pg}")["observations"]
    rows = sorted(
        (o["t_ms"] / 1000.0, o["raw_level"] * md["raw_scale"] + md["raw_offset"])
        for o in obs if o["valid"] == 1
    )
    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/observations.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time_s", "height_cm"])
        w.writerows(rows)
    return {"n_rows": len(rows)}


def _model(t, h_inf, k, h0):
    return h_inf + (h0 - h_inf) * np.exp(-k * t)


def fit():
    md = json.load(open(f"{OUT}/metadata.json"))
    h0 = md["column_height_cm"]
    df = pd.read_csv(f"{OUT}/observations.csv")
    t, h = df["time_s"].to_numpy(), df["height_cm"].to_numpy()
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
    report = {
        "experiment_id": EXPERIMENT_ID, "h_inf_cm": float(h_inf), "k_per_s": float(k),
        "h_inf_ci95": float(ci[0]), "k_ci95": float(ci[1]),
        "initial_velocity_cm_s": float(v0), "effective_diameter_um": float(d_um),
        "rmse": rmse, "r2": r2, "n_obs": int(len(t)),
    }
    os.makedirs(OUT, exist_ok=True)
    json.dump(report, open(f"{OUT}/report.json", "w"), indent=2)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["metadata", "observations", "fit"])
    print(json.dumps({"metadata": metadata, "observations": observations, "fit": fit}[ap.parse_args().command]()))
PY

python3 /app/sediment_cli.py metadata
