#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: write the full signal-analysis CLI to /app/signal_analysis.py
# (it persists in the shared container for milestones 2 and 3) and run its `query`
# subcommand, which reads every valid experiment from the DuckDB store and writes
# /app/artifacts/<id>/measurements.csv and metadata.json.
cat > /app/signal_analysis.py <<'PY'
#!/usr/bin/env python3
"""DuckDB + MLflow signal-analysis CLI.

Reads experimental sensor signals exclusively from a DuckDB database and, across
three subcommands, writes per-experiment sample CSVs (query), computes detrended
statistics / FFT-dominant frequencies / a bootstrap RMS confidence interval
(analyze), and records each analysis as an MLflow run (track).
"""

import argparse
import json
import os
import sys

import duckdb
import numpy as np
import scipy.signal
import scipy.stats

DEFAULT_DB = "/app/measurements.duckdb"
DEFAULT_OUTPUT_DIR = "/app/artifacts"
TRACKING_URI = "sqlite:////app/mlflow.db"
EXPERIMENT_NAME = "signal-analysis"
REGISTERED_MODEL = "signal_reconstruction"
SNR_THRESHOLD = 0.80

MC_SEED = 42
MC_ITERATIONS = 10000
MC_CHUNK = 1000
CONFIDENCE_LEVEL = 0.95


def resolve_experiments(con, requested):
    """Valid experiment ids to process; skip anything not present and valid."""
    valid = [
        row[0]
        for row in con.execute(
            "SELECT experiment_id FROM experiments WHERE status = 'valid' "
            "ORDER BY experiment_id"
        ).fetchall()
    ]
    if not requested:
        return valid
    valid_set = set(valid)
    chosen = []
    for exp in requested:
        if exp in valid_set:
            chosen.append(exp)
        else:
            print(f"skipping {exp}: not a valid experiment", file=sys.stderr)
    return chosen


def load_signal(con, experiment_id):
    """Return (sample_rate_hz, n_samples, sample_index array, signal array)."""
    sample_rate, n_samples = con.execute(
        "SELECT sample_rate_hz, n_samples FROM experiments WHERE experiment_id = ?",
        [experiment_id],
    ).fetchone()
    rows = con.execute(
        "SELECT sample_index, signal FROM measurements WHERE experiment_id = ? "
        "ORDER BY sample_index",
        [experiment_id],
    ).fetchall()
    indices = np.array([r[0] for r in rows], dtype=np.int64)
    signal = np.array([r[1] for r in rows], dtype=np.float64)
    return float(sample_rate), int(n_samples), indices, signal


def write_query_outputs(experiment_id, sample_rate, n_samples, indices, signal, output_dir):
    target = os.path.join(output_dir, experiment_id)
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, "measurements.csv"), "w") as fh:
        fh.write("sample_index,signal\n")
        for index, value in zip(indices, signal):
            fh.write(f"{int(index)},{float(value)!r}\n")
    with open(os.path.join(target, "metadata.json"), "w") as fh:
        json.dump(
            {
                "experiment_id": experiment_id,
                "sample_rate_hz": sample_rate,
                "n_samples": n_samples,
            },
            fh,
            indent=2,
        )


def compute_stats(detrended):
    return {
        "mean": float(np.mean(detrended)),
        "std": float(np.std(detrended)),
        "min": float(np.min(detrended)),
        "max": float(np.max(detrended)),
        "rms": float(np.sqrt(np.mean(detrended**2))),
        "skew": float(scipy.stats.skew(detrended)),
        "kurtosis": float(scipy.stats.kurtosis(detrended)),
    }


def dominant_frequencies(detrended, sample_rate, k=3):
    spectrum = np.abs(np.fft.rfft(detrended))
    freqs = np.fft.rfftfreq(detrended.shape[0], d=1.0 / sample_rate)
    spectrum[0] = 0.0
    order = np.argsort(spectrum)[::-1][:k]
    return [
        {
            "rank": rank + 1,
            "frequency_hz": float(freqs[idx]),
            "magnitude": float(spectrum[idx]),
        }
        for rank, idx in enumerate(order)
    ]


def bootstrap_rms_ci(detrended, seed=MC_SEED, n_iter=MC_ITERATIONS, level=CONFIDENCE_LEVEL):
    n = detrended.shape[0]
    rng = np.random.default_rng(seed)
    rms_samples = np.empty(n_iter, dtype=np.float64)
    for start in range(0, n_iter, MC_CHUNK):
        size = min(MC_CHUNK, n_iter - start)
        idx = rng.integers(0, n, size=(size, n))
        resampled = detrended[idx]
        rms_samples[start : start + size] = np.sqrt(np.mean(resampled**2, axis=1))
    lo_pct = (1.0 - level) / 2.0 * 100.0
    hi_pct = (1.0 + level) / 2.0 * 100.0
    low, high = np.percentile(rms_samples, [lo_pct, hi_pct])
    return float(low), float(high)


def analyze_signal(experiment_id, sample_rate, n_samples, signal):
    detrended = scipy.signal.detrend(signal, type="linear")
    low, high = bootstrap_rms_ci(detrended)
    return {
        "experiment_id": experiment_id,
        "n_samples": n_samples,
        "sample_rate_hz": sample_rate,
        "detrend": "linear",
        "stats": compute_stats(detrended),
        "dominant_frequencies": dominant_frequencies(detrended, sample_rate),
        "confidence_interval": {
            "statistic": "rms",
            "level": CONFIDENCE_LEVEL,
            "low": low,
            "high": high,
            "n_iterations": MC_ITERATIONS,
            "seed": MC_SEED,
        },
    }


def write_analysis(experiment_id, analysis, output_dir):
    target = os.path.join(output_dir, experiment_id)
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, "analysis.json"), "w") as fh:
        json.dump(analysis, fh, indent=2)


def write_summary(accepted_ids, rejected_ids, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    summary = {
        "accepted": sorted(accepted_ids),
        "rejected": sorted(rejected_ids),
        "n_accepted": len(accepted_ids),
        "n_valid": len(accepted_ids) + len(rejected_ids),
    }
    with open(os.path.join(output_dir, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)


def spectral_snr(detrended):
    spectrum = np.abs(np.fft.rfft(detrended))
    spectrum[0] = 0.0
    power = spectrum**2
    total = float(np.sum(power))
    if total == 0.0:
        return 0.0
    top = np.sort(power)[::-1][:3]
    return float(np.sum(top) / total)


def fit_reconstruction(detrended, sample_rate, freqs):
    from sklearn.linear_model import LinearRegression

    t = np.arange(detrended.shape[0], dtype=np.float64) / sample_rate
    cols = []
    for f in freqs:
        ang = 2.0 * np.pi * f * t
        cols.append(np.cos(ang))
        cols.append(np.sin(ang))
    design = np.column_stack(cols)
    return LinearRegression().fit(design, detrended)


def log_run(experiment_id, sample_rate, n_samples, signal, analysis, output_dir, mlflow, client):
    import mlflow.sklearn

    target = os.path.join(output_dir, experiment_id)
    detrended = scipy.signal.detrend(signal, type="linear")
    snr = spectral_snr(detrended)
    is_accepted = snr >= SNR_THRESHOLD
    with mlflow.start_run(run_name=experiment_id):
        mlflow.set_tag("experiment_id", experiment_id)
        mlflow.set_tag("tool", "duckdb-signal-analysis")
        mlflow.set_tag("status", "accepted" if is_accepted else "rejected")
        mlflow.log_param("experiment_id", experiment_id)
        mlflow.log_param("sample_rate_hz", sample_rate)
        mlflow.log_param("n_samples", n_samples)
        mlflow.log_param("detrend", "linear")
        mlflow.log_param("mc_seed", MC_SEED)
        mlflow.log_param("mc_iterations", MC_ITERATIONS)
        mlflow.log_param("confidence_level", CONFIDENCE_LEVEL)
        stats = analysis["stats"]
        for key in ("std", "rms", "skew", "kurtosis", "min", "max"):
            mlflow.log_metric(key, stats[key])
        freqs = [c["frequency_hz"] for c in analysis["dominant_frequencies"]]
        for component in analysis["dominant_frequencies"]:
            mlflow.log_metric(
                f"dominant_freq_{component['rank']}_hz", component["frequency_hz"]
            )
        interval = analysis["confidence_interval"]
        mlflow.log_metric("ci_rms_low", interval["low"])
        mlflow.log_metric("ci_rms_high", interval["high"])
        mlflow.log_metric("ci_rms_width", interval["high"] - interval["low"])
        mlflow.log_metric("spectral_snr", snr)
        mlflow.log_artifact(os.path.join(target, "measurements.csv"), artifact_path="analysis")
        mlflow.log_artifact(os.path.join(target, "analysis.json"), artifact_path="analysis")
        if is_accepted:
            model = fit_reconstruction(detrended, sample_rate, freqs)
            info = mlflow.sklearn.log_model(model, name="reconstruction_model")
            version = mlflow.register_model(info.model_uri, REGISTERED_MODEL)
            client.set_registered_model_alias(REGISTERED_MODEL, experiment_id, version.version)
            client.set_model_version_tag(
                REGISTERED_MODEL, version.version, "validation_status", "accepted"
            )
    return is_accepted


def main(argv=None):
    parser = argparse.ArgumentParser(description="DuckDB + MLflow signal analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("query", "analyze", "track"):
        sp = sub.add_parser(name)
        sp.add_argument("--experiment-id", action="append", dest="experiment_id")
        sp.add_argument("--db", default=DEFAULT_DB)
        sp.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    con = duckdb.connect(args.db, read_only=True)
    try:
        experiments = resolve_experiments(con, args.experiment_id)

        client = None
        if args.command == "track":
            import mlflow
            from mlflow.tracking import MlflowClient

            mlflow.set_tracking_uri(TRACKING_URI)
            mlflow.set_experiment(EXPERIMENT_NAME)
            client = MlflowClient()

        accepted_ids = []
        rejected_ids = []
        for experiment_id in experiments:
            sample_rate, n_samples, indices, signal = load_signal(con, experiment_id)
            if args.command == "query":
                write_query_outputs(
                    experiment_id, sample_rate, n_samples, indices, signal, args.output_dir
                )
            elif args.command == "analyze":
                analysis = analyze_signal(experiment_id, sample_rate, n_samples, signal)
                write_analysis(experiment_id, analysis, args.output_dir)
            elif args.command == "track":
                analysis = analyze_signal(experiment_id, sample_rate, n_samples, signal)
                write_query_outputs(
                    experiment_id, sample_rate, n_samples, indices, signal, args.output_dir
                )
                write_analysis(experiment_id, analysis, args.output_dir)
                is_accepted = log_run(
                    experiment_id, sample_rate, n_samples, signal, analysis,
                    args.output_dir, mlflow, client,
                )
                (accepted_ids if is_accepted else rejected_ids).append(experiment_id)
            print(f"{args.command}: {experiment_id}")

        if args.command == "track":
            write_summary(accepted_ids, rejected_ids, args.output_dir)
    finally:
        con.close()


if __name__ == "__main__":
    main()
PY

python3 /app/signal_analysis.py query
