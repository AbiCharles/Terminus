"""Independent reference implementation for the signal-analysis task.

This module recomputes, directly from the DuckDB store at /app/measurements.duckdb,
the canonical answers the agent's tool must produce: which experiments are valid,
each experiment's raw samples, and (for later milestones) the detrended statistics,
FFT-dominant frequencies, and bootstrap RMS confidence interval. It is the
verifier's answer key. It never reads the agent's /app/artifacts or MLflow store,
so an agent cannot weaken verification by tampering with its own outputs, and the
agent has no access to this module at solve time.

The numerical conventions here (linear detrend, rfft magnitudes excluding DC, and
the seeded chunked bootstrap of the RMS) are the binding definitions of the task's
deterministic outputs.
"""

import duckdb
import numpy as np
import scipy.signal
import scipy.stats

DB_PATH = "/app/measurements.duckdb"

MC_SEED = 42
MC_ITERATIONS = 10000
MC_CHUNK = 1000
CONFIDENCE_LEVEL = 0.95


def valid_experiment_ids(db_path=DB_PATH):
    """Return the sorted ids of experiments whose status is 'valid'."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        rows = con.execute(
            "SELECT experiment_id FROM experiments WHERE status = 'valid' "
            "ORDER BY experiment_id"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def nonvalid_experiment_ids(db_path=DB_PATH):
    """Return the sorted ids of experiments whose status is not 'valid'."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        rows = con.execute(
            "SELECT experiment_id FROM experiments WHERE status <> 'valid' "
            "ORDER BY experiment_id"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def experiment_metadata(experiment_id, db_path=DB_PATH):
    """Return (sample_rate_hz, n_samples, status) for one experiment."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        row = con.execute(
            "SELECT sample_rate_hz, n_samples, status FROM experiments "
            "WHERE experiment_id = ?",
            [experiment_id],
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    return float(row[0]), int(row[1]), row[2]


def load_signal(experiment_id, db_path=DB_PATH):
    """Return the experiment's signal as a float array ordered by sample_index."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        rows = con.execute(
            "SELECT signal FROM measurements WHERE experiment_id = ? "
            "ORDER BY sample_index",
            [experiment_id],
        ).fetchall()
    finally:
        con.close()
    return np.array([r[0] for r in rows], dtype=np.float64)


def detrend(signal):
    """Linearly detrend the signal (removes the best-fit line, including mean)."""
    return scipy.signal.detrend(signal, type="linear")


def compute_stats(detrended):
    """Basic statistics of the detrended signal."""
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
    """The k strongest FFT components (excluding DC), strongest first."""
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
    """Seeded bootstrap confidence interval for the RMS of the detrended signal.

    Resamples the detrended signal with replacement n_iter times using numpy's
    default RNG seeded at `seed`, computes the RMS of each resample, and returns
    the central `level` percentile interval. Drawn in fixed-size chunks purely
    to bound memory; the RNG stream is identical to a single contiguous draw.
    """
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


def compute_analysis(experiment_id, db_path=DB_PATH):
    """Full canonical analysis for one experiment, mirroring analysis.json."""
    sample_rate, n_samples, _status = experiment_metadata(experiment_id, db_path)
    signal = load_signal(experiment_id, db_path)
    detrended = detrend(signal)
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
