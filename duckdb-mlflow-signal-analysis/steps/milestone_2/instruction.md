Next, add an `analyze` subcommand to /app/signal_analysis.py so `python /app/signal_analysis.py analyze` computes signal statistics for each valid experiment and writes /app/artifacts/<experiment_id>/analysis.json. Keep the same subcommand options as query — `--db` (default `/app/measurements.duckdb`), `--output-dir` (default `/app/artifacts`) and repeatable `--experiment-id` — e.g. `python /app/signal_analysis.py analyze --db /app/measurements.duckdb --output-dir /app/artifacts`; the data still comes only from the DuckDB store.

Do the work on the linearly detrended signal (remove the linear trend before computing anything). Report the basic stats (mean, std, min, max, rms, skew, and excess/Fisher kurtosis), the three dominant frequency components from the FFT — each with its frequency in Hz using the experiment's sample rate and its magnitude, strongest first — and a 95% bootstrap confidence interval for the RMS built from 10000 resamples with replacement using numpy's default RNG seeded at 42.

Write analysis.json shaped exactly like this:

```json
{
  "experiment_id": "<string>",
  "n_samples": <int>,
  "sample_rate_hz": <float>,
  "detrend": "linear",
  "stats": {"mean": <float>, "std": <float>, "min": <float>, "max": <float>, "rms": <float>, "skew": <float>, "kurtosis": <float>},
  "dominant_frequencies": [{"rank": <int>, "frequency_hz": <float>, "magnitude": <float>}, {"rank": <int>, "frequency_hz": <float>, "magnitude": <float>}, {"rank": <int>, "frequency_hz": <float>, "magnitude": <float>}],
  "confidence_interval": {"statistic": "rms", "level": 0.95, "low": <float>, "high": <float>, "n_iterations": 10000, "seed": 42}
}
```
