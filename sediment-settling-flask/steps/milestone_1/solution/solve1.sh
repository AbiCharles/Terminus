#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the full sediment_cli.py and run its `metadata`
# subcommand to produce /app/output/metadata.json for experiment 7.
cat > /app/sediment_cli.py <<'PY'
"""Sediment settling-column inference CLI."""
import argparse
import csv
import json
import os
import sqlite3

import numpy as np
import pandas as pd
import requests
from scipy.optimize import curve_fit

DB_PATH = "/app/experiments.db"
API_BASE = "http://127.0.0.1:8000"
OUT_DIR = "/app/output"
G = 9.81
MIN_SIDE = 5

META_KEYS = [
    "experiment_id", "label", "column_height_cm", "fluid_viscosity_pa_s",
    "fluid_density_kg_m3", "particle_density_kg_m3", "temperature_c",
    "raw_scale", "raw_offset",
]


def get_metadata(experiment_id):
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
        resp = requests.get(
            f"{API_BASE}/experiments/{experiment_id}/{endpoint}",
            params={"page": page}, timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        for item in payload[key]:
            out[item["seq"]] = item
        if payload["next"] is None:
            break
        page = payload["next"]
    return out


def joined_observations(experiment_id, meta):
    ts = _fetch_all(experiment_id, "timestamps", "timestamps")
    lv = _fetch_all(experiment_id, "levels", "levels")
    rows = []
    for seq, t in ts.items():
        if seq in lv:
            time_s = t["t_ms"] / 1000.0
            height_cm = lv[seq]["raw_level"] * meta["raw_scale"] + meta["raw_offset"]
            rows.append((time_s, height_cm))
    rows.sort()
    return rows


def cmd_metadata(experiment_id):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "metadata.json"), "w") as fh:
        json.dump(get_metadata(experiment_id), fh, indent=2)


def cmd_observations(experiment_id):
    meta = get_metadata(experiment_id)
    rows = joined_observations(experiment_id, meta)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "observations.csv"), "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["time_s", "height_cm"])
        writer.writerows(rows)


def _two_phase_fit(meta, t, h):
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
    return best


def cmd_fit(experiment_id):
    meta = get_metadata(experiment_id)
    df = pd.read_csv(os.path.join(OUT_DIR, "observations.csv"))
    t = df["time_s"].to_numpy()
    h = df["height_cm"].to_numpy()
    best = _two_phase_fit(meta, t, h)
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
    parser.add_argument("command", choices=["metadata", "observations", "fit"])
    parser.add_argument("--experiment-id", type=int, required=True)
    args = parser.parse_args()
    {"metadata": cmd_metadata, "observations": cmd_observations, "fit": cmd_fit}[args.command](
        args.experiment_id
    )


if __name__ == "__main__":
    main()
PY

python3 /app/sediment_cli.py metadata --experiment-id 7
