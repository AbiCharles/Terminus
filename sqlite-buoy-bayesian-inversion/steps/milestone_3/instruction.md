Finally, add an `invert` subcommand so `python /app/buoy_calibrate.py invert` runs the Bayesian inversion for each calibrated buoy. Model the cleaned residual as residual = offset + drift·t_days + noise, with the offset and drift given the independent Gaussian priors from the protocol and the noise being zero-mean Gaussian with the per-sensor-type standard deviation (treated as known). Combine the priors with the Gaussian likelihood to get the closed-form conjugate posterior over offset and drift — no sampling needed.

Write /app/artifacts/<buoy_id>/posterior.json with this shape:

```json
{
  "buoy_id": "<string>",
  "sensor_type": "<string>",
  "n_observations": <int>,
  "posterior": {
    "offset": {"mean": <float>, "std": <float>},
    "drift": {"mean": <float>, "std": <float>}
  },
  "credible_interval_95": {"offset": [<float>, <float>], "drift": [<float>, <float>]},
  "calibration": {"rmse_residual": <float>, "corrected_rmse": <float>}
}
```

The credible interval is the central 95% interval of each parameter's posterior. rmse_residual is the root-mean-square residual before correction, and corrected_rmse is the root-mean-square of residual minus the posterior offset and drift. Also write /app/artifacts/summary.json with a "buoys" list (one entry per calibrated buoy carrying at least its buoy_id and corrected_rmse) and a "fleet" object holding "n_buoys" and "mean_corrected_rmse" across the calibrated fleet.
