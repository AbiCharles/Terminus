#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the full buoy-calibration CLI to /app/buoy_calibrate.py
# (it persists in the shared container for milestones 2 and 3) and run its `parse`
# subcommand, which extracts the binding calibration protocol from the mission
# notebook into /app/protocol.json.
cat > /app/buoy_calibrate.py <<'PY'
#!/usr/bin/env python3
"""Ocean-buoy sensor-drift calibration CLI (SQLite + Bayesian inversion).

Three subcommands:
  parse   extract the binding calibration protocol from the mission notebook
  query   write the cleaned residual series per buoy from the SQLite store
  invert  compute the conjugate Gaussian posterior for offset and drift
"""

import argparse
import csv
import json
import os
import re
import sqlite3
from datetime import datetime, timezone

import numpy as np

TS = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
Z95 = 1.959963984540054


# --------------------------------------------------------------------------- parse
def parse_notebook(path):
    raw = open(path, encoding="utf-8").read()
    # Only the governing sections (§6 through §13) are binding; everything from
    # §14 onward (and the §1-§5 front matter) is background and carries superseded
    # distractor values.
    governing = raw[raw.index("## §6"):raw.index("## §14")]
    flat = re.sub(r"\s+", " ", governing)

    def find(pattern, group=1, cast=str):
        m = re.search(pattern, flat)
        if not m:
            raise SystemExit(f"protocol extraction failed: {pattern}")
        return cast(m.group(group))

    epoch = find(rf"mission epoch is fixed at ({TS})")
    active_status = find(r"operational status is (\w+)")
    inc_segment = find(r"Only (.+?) sensor channels are included")
    included = re.findall(r"temperature|pressure|salinity", inc_segment)

    dec = r"-?[0-9]+\.[0-9]+"
    sensors = {}
    sensors["temperature"] = {
        "unit_conversion": find(rf"Temperature raw counts .*? multiplying by ({dec})", cast=float),
        "noise_std": find(rf"noise standard deviation is ({dec}) for temperature", cast=float),
    }
    sensors["pressure"] = {
        "unit_conversion": find(rf"Pressure raw counts .*? multiplying by ({dec})", cast=float),
        "noise_std": find(rf"and ({dec}) for pressure", cast=float),
    }
    for stype in ("temperature", "pressure"):
        m = re.search(
            rf"For {stype}, the offset prior is Gaussian with mean ({dec}) and standard "
            rf"deviation ({dec}), and the drift prior is Gaussian with mean ({dec}) and "
            rf"standard deviation ({dec})",
            flat,
        )
        if not m:
            raise SystemExit(f"prior extraction failed for {stype}")
        sensors[stype]["priors"] = {
            "offset": {"mean": float(m.group(1)), "std": float(m.group(2))},
            "drift": {"mean": float(m.group(3)), "std": float(m.group(4))},
        }

    exclusions = []
    fleet = re.search(rf"fleet-wide maintenance exclusion applies to all buoys from ({TS}) to ({TS})", flat)
    if fleet:
        exclusions.append({"buoy_id": "ALL", "start": fleet.group(1), "end": fleet.group(2)})
    for m in re.finditer(rf"exclusion applies to buoy (\w+) from ({TS}) to ({TS})", flat):
        exclusions.append({"buoy_id": m.group(1), "start": m.group(2), "end": m.group(3)})

    return {
        "mission_epoch": epoch,
        "time_unit": "days",
        "active_status": active_status,
        "included_sensor_types": included,
        "sensors": sensors,
        "exclusion_intervals": exclusions,
    }


# ------------------------------------------------------------------------ utilities
def _parse_ts(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _excluded(buoy_id, ts_dt, intervals):
    for iv in intervals:
        if iv["buoy_id"] in ("ALL", buoy_id):
            if _parse_ts(iv["start"]) <= ts_dt < _parse_ts(iv["end"]):
                return True
    return False


def included_buoys(con, protocol):
    rows = con.execute(
        "SELECT buoy_id, sensor_type FROM buoys WHERE status = ? ORDER BY buoy_id",
        (protocol["active_status"],),
    ).fetchall()
    included = set(protocol["included_sensor_types"])
    return [(b, s) for b, s in rows if s in included]


def clean_series(con, buoy_id, sensor_type, protocol):
    scale = protocol["sensors"][sensor_type]["unit_conversion"]
    epoch = _parse_ts(protocol["mission_epoch"])
    intervals = protocol["exclusion_intervals"]
    rows = con.execute(
        "SELECT timestamp, raw_reading, reference_reading FROM observations "
        "WHERE buoy_id = ? ORDER BY timestamp",
        (buoy_id,),
    ).fetchall()
    series = {"timestamp": [], "t_days": [], "converted_value": [], "reference_value": [], "residual": []}
    for ts, raw, ref in rows:
        ts_dt = _parse_ts(ts)
        if _excluded(buoy_id, ts_dt, intervals):
            continue
        converted = raw * scale
        series["timestamp"].append(ts)
        series["t_days"].append((ts_dt - epoch).total_seconds() / 86400.0)
        series["converted_value"].append(converted)
        series["reference_value"].append(ref)
        series["residual"].append(converted - ref)
    return series


def compute_posterior(series, sensor_type, protocol):
    t = np.array(series["t_days"], dtype=np.float64)
    r = np.array(series["residual"], dtype=np.float64)
    n = t.shape[0]
    priors = protocol["sensors"][sensor_type]["priors"]
    noise_std = protocol["sensors"][sensor_type]["noise_std"]
    m0 = np.array([priors["offset"]["mean"], priors["drift"]["mean"]], dtype=np.float64)
    s0_inv = np.diag([1.0 / priors["offset"]["std"] ** 2, 1.0 / priors["drift"]["std"] ** 2])
    sigma2 = noise_std ** 2
    design = np.column_stack([np.ones(n), t])
    sn = np.linalg.inv(s0_inv + design.T @ design / sigma2)
    mn = sn @ (s0_inv @ m0 + design.T @ r / sigma2)
    offset_mean, drift_mean = float(mn[0]), float(mn[1])
    offset_std, drift_std = float(np.sqrt(sn[0, 0])), float(np.sqrt(sn[1, 1]))
    corrected = r - (offset_mean + drift_mean * t)
    return {
        "buoy_id": None,
        "sensor_type": sensor_type,
        "n_observations": int(n),
        "posterior": {
            "offset": {"mean": offset_mean, "std": offset_std},
            "drift": {"mean": drift_mean, "std": drift_std},
        },
        "credible_interval_95": {
            "offset": [offset_mean - Z95 * offset_std, offset_mean + Z95 * offset_std],
            "drift": [drift_mean - Z95 * drift_std, drift_mean + Z95 * drift_std],
        },
        "calibration": {
            "rmse_residual": float(np.sqrt(np.mean(r**2))),
            "corrected_rmse": float(np.sqrt(np.mean(corrected**2))),
        },
    }


def write_clean_csv(path, series):
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "t_days", "converted_value", "reference_value", "residual"])
        for i in range(len(series["timestamp"])):
            writer.writerow([
                series["timestamp"][i],
                repr(series["t_days"][i]),
                repr(series["converted_value"][i]),
                repr(series["reference_value"][i]),
                repr(series["residual"][i]),
            ])


# ----------------------------------------------------------------------------- main
def main(argv=None):
    parser = argparse.ArgumentParser(description="Buoy sensor-drift calibration")
    sub = parser.add_subparsers(dest="command", required=True)

    p_parse = sub.add_parser("parse")
    p_parse.add_argument("--notebook", default="/app/mission_notebook.md")
    p_parse.add_argument("--out", default="/app/protocol.json")

    for name in ("query", "invert"):
        sp = sub.add_parser(name)
        sp.add_argument("--db", default="/app/observations.db")
        sp.add_argument("--protocol", default="/app/protocol.json")
        sp.add_argument("--output-dir", default="/app/artifacts")

    args = parser.parse_args(argv)

    if args.command == "parse":
        protocol = parse_notebook(args.notebook)
        with open(args.out, "w") as fh:
            json.dump(protocol, fh, indent=2)
        print(f"parse: wrote {args.out}")
        return

    with open(args.protocol) as fh:
        protocol = json.load(fh)
    con = sqlite3.connect(args.db)
    try:
        buoys = included_buoys(con, protocol)
        if args.command == "query":
            for buoy_id, sensor_type in buoys:
                target = os.path.join(args.output_dir, buoy_id)
                os.makedirs(target, exist_ok=True)
                series = clean_series(con, buoy_id, sensor_type, protocol)
                write_clean_csv(os.path.join(target, "clean.csv"), series)
                print(f"query: {buoy_id} ({len(series['timestamp'])} rows)")
        elif args.command == "invert":
            summary = {"buoys": [], "fleet": {}}
            for buoy_id, sensor_type in buoys:
                target = os.path.join(args.output_dir, buoy_id)
                os.makedirs(target, exist_ok=True)
                series = clean_series(con, buoy_id, sensor_type, protocol)
                result = compute_posterior(series, sensor_type, protocol)
                result["buoy_id"] = buoy_id
                with open(os.path.join(target, "posterior.json"), "w") as fh:
                    json.dump(result, fh, indent=2)
                summary["buoys"].append({
                    "buoy_id": buoy_id,
                    "sensor_type": sensor_type,
                    "n_observations": result["n_observations"],
                    "offset_mean": result["posterior"]["offset"]["mean"],
                    "drift_mean": result["posterior"]["drift"]["mean"],
                    "rmse_residual": result["calibration"]["rmse_residual"],
                    "corrected_rmse": result["calibration"]["corrected_rmse"],
                })
                print(f"invert: {buoy_id}")
            rmses = [b["corrected_rmse"] for b in summary["buoys"]]
            summary["fleet"] = {
                "n_buoys": len(summary["buoys"]),
                "mean_corrected_rmse": float(np.mean(rmses)) if rmses else 0.0,
            }
            with open(os.path.join(args.output_dir, "summary.json"), "w") as fh:
                json.dump(summary, fh, indent=2)
    finally:
        con.close()


if __name__ == "__main__":
    main()
PY

python3 /app/buoy_calibrate.py parse
