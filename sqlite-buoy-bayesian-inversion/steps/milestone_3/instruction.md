Finally, add an `invert` subcommand so `python /app/buoy_calibrate.py invert` runs the Bayesian inversion for each calibrated buoy. The cleaned residual follows a change-point drift model:

    residual(t) = offset + drift * t + drift_change * max(0, t - t_changepoint) + noise

where t is elapsed days since the mission epoch and t_changepoint is the protocol's drift changepoint expressed in elapsed days. The noise is independent zero-mean Gaussian but heteroscedastic: observation i has its own known standard deviation (the measurement_std column), so the inversion must be weighted by the inverse of each observation's variance rather than treating the noise as constant. Put independent Gaussian priors on the three parameters from the protocol (offset, drift, drift_change for that sensor type) and report the conjugate Gaussian posterior — its mean and standard deviation for each parameter and a central 95% credible interval. No sampling is needed; the posterior is available in closed form for this weighted linear-Gaussian model.

Write /app/artifacts/<buoy_id>/posterior.json with this shape:

```json
{
  "buoy_id": "<string>",
  "sensor_type": "<string>",
  "n_observations": <int>,
  "changepoint_t_days": <float>,
  "posterior": {
    "offset": {"mean": <float>, "std": <float>},
    "drift": {"mean": <float>, "std": <float>},
    "drift_change": {"mean": <float>, "std": <float>}
  },
  "credible_interval_95": {"offset": [<float>, <float>], "drift": [<float>, <float>], "drift_change": [<float>, <float>]},
  "calibration": {"rmse_residual": <float>, "corrected_rmse": <float>}
}
```

changepoint_t_days is t_changepoint in elapsed days. rmse_residual is the root-mean-square residual before correction, and corrected_rmse is the root-mean-square of the residual after subtracting the fitted offset, drift and drift_change terms. Also write /app/artifacts/summary.json with a "buoys" list (one entry per calibrated buoy carrying at least its buoy_id and corrected_rmse) and a "fleet" object holding "n_buoys" and "mean_corrected_rmse" across the calibrated fleet.

Finally, register each buoy's calibration as a model in MLflow so it can be deployed. Use a local sqlite tracking store at sqlite:////app/mlflow.db with artifacts under /app/mlruns and an experiment named buoy-calibration. For each calibrated buoy, in a run named after the buoy, log sensor_type, n_observations and changepoint_t_days as params and the posterior means and stds as metrics, then log the fitted drift-correction model with mlflow.sklearn.log_model — a model that, given the two features [t_days, hinge] where hinge = max(0, t_days - changepoint_t_days), returns the correction offset + drift*t_days + drift_change*hinge. Register that logged model as a version of a single registered model named buoy_drift_correction and assign it the buoy's id as its registry alias, so that models:/buoy_drift_correction@<buoy_id> resolves to that buoy's calibration model.
