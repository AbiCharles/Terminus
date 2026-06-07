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


SNR_THRESHOLD = 0.80


def spectral_snr(detrended):
    """Concentrated spectral SNR: fraction of detrended FFT power (excluding DC)
    carried by the three strongest components. A clean multi-tone signal packs
    almost all its power into those bins (SNR near 1); a noise-dominated run
    spreads power across the spectrum (low SNR)."""
    spectrum = np.abs(np.fft.rfft(detrended))
    spectrum[0] = 0.0
    power = spectrum**2
    total = float(np.sum(power))
    if total == 0.0:
        return 0.0
    top = np.sort(power)[::-1][:3]
    return float(np.sum(top) / total)


def accepted(experiment_id, db_path=DB_PATH):
    """Acceptance gate: a valid experiment is accepted iff its concentrated
    spectral SNR is at least SNR_THRESHOLD."""
    sample_rate, _n, _status = experiment_metadata(experiment_id, db_path)
    detrended = detrend(load_signal(experiment_id, db_path))
    return spectral_snr(detrended) >= SNR_THRESHOLD


def reconstruction_features(t_seconds, freqs):
    """Fourier design matrix: for each frequency, the [cos, sin] pair at the given
    times, in frequency order (rank 1..3), giving 2*len(freqs) columns."""
    t = np.asarray(t_seconds, dtype=np.float64)
    cols = []
    for f in freqs:
        ang = 2.0 * np.pi * f * t
        cols.append(np.cos(ang))
        cols.append(np.sin(ang))
    return np.column_stack(cols)


def reconstruction_fit(experiment_id, db_path=DB_PATH):
    """Independent OLS fit of the Fourier reconstruction model used to validate the
    agent's registered model: target is the detrended signal, features are the
    [cos, sin] pairs of the three dominant frequencies at each sample's time
    (sample_index / sample_rate). Returns intercept, coefficients and the freqs."""
    sample_rate, _n, _status = experiment_metadata(experiment_id, db_path)
    detrended = detrend(load_signal(experiment_id, db_path))
    freqs = [c["frequency_hz"] for c in dominant_frequencies(detrended, sample_rate)]
    t = np.arange(detrended.shape[0], dtype=np.float64) / sample_rate
    design = reconstruction_features(t, freqs)
    augmented = np.column_stack([np.ones(design.shape[0]), design])
    beta, _res, _rank, _sv = np.linalg.lstsq(augmented, detrended, rcond=None)
    return {
        "freqs": freqs,
        "sample_rate": sample_rate,
        "intercept": float(beta[0]),
        "coef": [float(c) for c in beta[1:]],
    }


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
