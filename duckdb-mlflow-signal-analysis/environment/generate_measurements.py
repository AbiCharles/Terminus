"""Build the seeded DuckDB sensor-measurement database used by the task.

Run at image-build time only (in a throwaway builder stage); the agent never
sees this script. Each experiment's signal is a sum of fixed sinusoids whose
frequencies land exactly on FFT bins, plus a linear trend and seeded Gaussian
noise, so the detrended statistics, dominant frequencies, and bootstrap
confidence intervals computed from the database are fully deterministic.
"""

import sys

import duckdb
import numpy as np

# Each valid experiment: (id, sample_rate_hz, n_samples, [(freq_hz, amplitude)],
# trend_slope_per_sample, trend_intercept, noise_std). Frequencies are chosen so
# that freq = k * sample_rate / n_samples for integer k (exact FFT bins).
VALID = [
    ("EXP001", 1000.0, 2000, [(50.0, 4.0), (120.0, 2.5), (25.0, 1.5)], 0.002, 5.0, 0.40),
    ("EXP002", 2000.0, 4000, [(80.0, 3.5), (200.0, 2.0), (310.0, 1.2)], -0.001, -3.0, 0.50),
    ("EXP003", 500.0, 2500, [(30.0, 3.0), (75.0, 2.2), (110.0, 1.0)], 0.004, 2.0, 2.60),
    ("EXP004", 1000.0, 3000, [(60.0, 3.2), (150.0, 2.8), (15.0, 1.8)], 0.0, 10.0, 0.45),
    ("EXP005", 2000.0, 4000, [(220.0, 4.5), (500.0, 3.0), (110.0, 1.5)], -0.003, 0.0, 3.20),
    ("EXP006", 800.0, 3200, [(40.0, 3.8), (96.0, 2.4), (160.0, 1.6)], 0.0015, -1.0, 2.90),
]

# Non-valid experiments still carry rows, but their status excludes them from
# analysis. They exist so the tool's status filtering is exercised.
INVALID = [
    ("EXP007", "quarantined", 1000.0, 2000, [(70.0, 2.0)], 0.0, 0.0, 0.5),
    ("EXP008", "failed", 1000.0, 512, [(100.0, 2.0)], 0.0, 0.0, 0.5),
]


def synthesize(sample_rate, n, components, slope, intercept, noise_std, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    signal = np.zeros(n, dtype=np.float64)
    for freq, amplitude in components:
        signal += amplitude * np.sin(2.0 * np.pi * freq * t / sample_rate)
    signal += slope * t + intercept
    signal += rng.normal(0.0, noise_std, size=n)
    return signal


def main(db_path):
    con = duckdb.connect(db_path)
    con.execute(
        "CREATE TABLE experiments ("
        "experiment_id VARCHAR, sample_rate_hz DOUBLE, n_samples INTEGER, "
        "status VARCHAR, description VARCHAR)"
    )
    con.execute(
        "CREATE TABLE measurements ("
        "experiment_id VARCHAR, sample_index INTEGER, signal DOUBLE)"
    )

    seed = 1000
    for exp_id, sample_rate, n, comps, slope, intercept, noise in VALID:
        signal = synthesize(sample_rate, n, comps, slope, intercept, noise, seed)
        seed += 1
        con.execute(
            "INSERT INTO experiments VALUES (?, ?, ?, 'valid', ?)",
            [exp_id, sample_rate, n, f"sensor run {exp_id}"],
        )
        con.executemany(
            "INSERT INTO measurements VALUES (?, ?, ?)",
            [[exp_id, int(i), float(v)] for i, v in enumerate(signal)],
        )

    for exp_id, status, sample_rate, n, comps, slope, intercept, noise in INVALID:
        signal = synthesize(sample_rate, n, comps, slope, intercept, noise, seed)
        seed += 1
        con.execute(
            "INSERT INTO experiments VALUES (?, ?, ?, ?, ?)",
            [exp_id, sample_rate, n, status, f"sensor run {exp_id} ({status})"],
        )
        con.executemany(
            "INSERT INTO measurements VALUES (?, ?, ?)",
            [[exp_id, int(i), float(v)] for i, v in enumerate(signal)],
        )

    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "measurements.duckdb")
