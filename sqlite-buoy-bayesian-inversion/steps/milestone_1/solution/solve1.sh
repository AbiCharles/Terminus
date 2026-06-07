#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the full buoy-calibration CLI to /app/buoy_calibrate.py
# (it persists in the shared container for milestones 2 and 3) and run its `parse`
# subcommand, which extracts the binding calibration protocol from the mission
# notebook into /app/protocol.json.
cat > /app/buoy_calibrate.py <<'PY'
#!/usr/bin/env python3
"""Ocean-buoy sensor-drift calibration CLI (SQLite + weighted change-point Bayesian inversion).

Subcommands:
  parse   extract the binding calibration protocol from the mission notebook
  query   write the cleaned residual series per buoy from the SQLite store
  invert  fit the heteroscedastic three-parameter change-point Gaussian posterior
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
DEC = r"-?[0-9]+\.[0-9]+"
Z95 = 1.959963984540054
PARAMS = ("offset", "drift", "drift_change")


def parse_notebook(path):
    raw = open(path, encoding="utf-8").read()
    governing = raw[raw.index("## §6"):raw.index("## §14")]
    flat = re.sub(r"\s+", " ", governing)

    def find(pattern, cast=str):
        m = re.search(pattern, flat)
        if not m:
            raise SystemExit(f"protocol extraction failed: {pattern}")
        return cast(m.group(1))

    epoch = find(rf"mission epoch is fixed at ({TS})")
    changepoint = find(rf"drift changepoint at ({TS})")
    active_status = find(r"operational status is (\w+)")
    included = re.findall(r"temperature|pressure|salinity", find(r"Only (.+?) sensor channels are included"))

    sensors = {}
    sensors["temperature"] = {"unit_conversion": find(rf"Temperature raw counts .*? multiplying by ({DEC})", float)}
    sensors["pressure"] = {"unit_conversion": find(rf"Pressure raw counts .*? multiplying by ({DEC})", float)}
    for stype in ("temperature", "pressure"):
        m = re.search(
            rf"For {stype}, the offset prior is Gaussian with mean ({DEC}) and standard deviation ({DEC}), "
            rf"the drift prior is Gaussian with mean ({DEC}) and standard deviation ({DEC}), and the "
            rf"drift-change prior is Gaussian with mean ({DEC}) and standard deviation ({DEC})",
            flat,
        )
        if not m:
            raise SystemExit(f"prior extraction failed for {stype}")
        g = [float(x) for x in m.groups()]
        sensors[stype]["priors"] = {
            "offset": {"mean": g[0], "std": g[1]},
            "drift": {"mean": g[2], "std": g[3]},
            "drift_change": {"mean": g[4], "std": g[5]},
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
        "drift_changepoint": changepoint,
        "sensors": sensors,
        "exclusion_intervals": exclusions,
    }


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
        "SELECT timestamp, raw_reading, reference_reading, measurement_std FROM observations "
        "WHERE buoy_id = ? ORDER BY timestamp",
        (buoy_id,),
    ).fetchall()
    s = {k: [] for k in ("timestamp", "t_days", "converted_value", "reference_value", "residual", "measurement_std")}
    for ts, raw, ref, std in rows:
        ts_dt = _parse_ts(ts)
        if _excluded(buoy_id, ts_dt, intervals):
            continue
        converted = raw * scale
        s["timestamp"].append(ts)
        s["t_days"].append((ts_dt - epoch).total_seconds() / 86400.0)
        s["converted_value"].append(converted)
        s["reference_value"].append(ref)
        s["residual"].append(converted - ref)
        s["measurement_std"].append(std)
    return s


def changepoint_t_days(protocol):
    return (_parse_ts(protocol["drift_changepoint"]) - _parse_ts(protocol["mission_epoch"])).total_seconds() / 86400.0


def compute_posterior(series, sensor_type, protocol):
    t = np.array(series["t_days"], dtype=np.float64)
    r = np.array(series["residual"], dtype=np.float64)
    std = np.array(series["measurement_std"], dtype=np.float64)
    n = t.shape[0]
    t_change = changepoint_t_days(protocol)
    hinge = np.maximum(0.0, t - t_change)
    design = np.column_stack([np.ones(n), t, hinge])
    w = 1.0 / std**2
    atwa = design.T @ (design * w[:, None])
    atwr = design.T @ (r * w)
    priors = protocol["sensors"][sensor_type]["priors"]
    m0 = np.array([priors[p]["mean"] for p in PARAMS], dtype=np.float64)
    s0_inv = np.diag([1.0 / priors[p]["std"] ** 2 for p in PARAMS])
    sn = np.linalg.inv(s0_inv + atwa)
    mn = sn @ (s0_inv @ m0 + atwr)
    sds = np.sqrt(np.diag(sn))
    corrected = r - design @ mn
    return {
        "buoy_id": None,
        "sensor_type": sensor_type,
        "n_observations": int(n),
        "changepoint_t_days": float(t_change),
        "posterior": {p: {"mean": float(mn[i]), "std": float(sds[i])} for i, p in enumerate(PARAMS)},
        "credible_interval_95": {
            p: [float(mn[i] - Z95 * sds[i]), float(mn[i] + Z95 * sds[i])] for i, p in enumerate(PARAMS)
        },
        "calibration": {
            "rmse_residual": float(np.sqrt(np.mean(r**2))),
            "corrected_rmse": float(np.sqrt(np.mean(corrected**2))),
        },
    }


def write_clean_csv(path, series):
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "t_days", "converted_value", "reference_value", "residual", "measurement_std"])
        for i in range(len(series["timestamp"])):
            writer.writerow([
                series["timestamp"][i],
                repr(series["t_days"][i]),
                repr(series["converted_value"][i]),
                repr(series["reference_value"][i]),
                repr(series["residual"][i]),
                repr(series["measurement_std"][i]),
            ])


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
                write_clean_csv(os.path.join(target, "clean.csv"), clean_series(con, buoy_id, sensor_type, protocol))
                print(f"query: {buoy_id}")
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
                    "drift_change_mean": result["posterior"]["drift_change"]["mean"],
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
