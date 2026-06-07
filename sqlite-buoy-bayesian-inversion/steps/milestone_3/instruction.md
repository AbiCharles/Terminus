Finally, add an `invert` subcommand so `python /app/buoy_calibrate.py invert` runs the Bayesian inversion for each calibrated buoy. The cleaned residual follows a change-point drift model:

    residual(t) = offset + drift * t + drift_change * max(0, t - t_changepoint) + noise

where t is elapsed days since the mission epoch and t_changepoint is the protocol's drift changepoint expressed in elapsed days. The noise is independent zero-mean Gaussian but heteroscedastic: observation i has its own known standard deviation (the measurement_std column), so the inversion must be weighted by the inverse of each observation's variance rather than treating the noise as constant. Pick each buoy's priors by its sensor type (the sensor_type carried in clean.csv, or the buoys table) and put the protocol's independent Gaussian priors on the three parameters (offset, drift, drift_change). Report the conjugate Gaussian posterior — its mean and standard deviation for each parameter and a central 95% credible interval. No sampling is needed; the posterior is available in closed form for this weighted linear-Gaussian model.

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

Finally, record the calibration in MLflow and register the deployable models. Use a local sqlite tracking store at sqlite:////app/mlflow.db with artifacts under /app/mlruns and an experiment named buoy-calibration. For every calibrated buoy, in a run named after the buoy, log sensor_type, n_observations and changepoint_t_days as params and the posterior means and stds as metrics (offset_mean, offset_std, drift_mean, drift_std, drift_change_mean, drift_change_std, corrected_rmse), and set a buoy_id tag equal to the buoy id.

Apply this acceptance gate: a buoy's calibration is accepted only if its drift_change is statistically resolved — its 95% credible interval for drift_change excludes zero — and is rejected otherwise. Tag each run with a status of accepted or rejected accordingly.

For each accepted buoy, build a scikit-learn Pipeline that, given the two features [t_days, hinge] where hinge = max(0, t_days - changepoint_t_days), predicts the correction offset + drift*t_days + drift_change*hinge. The estimator you register must be a genuinely fitted scikit-learn estimator: when the model is reloaded from the registry and `.predict()` is called it must return values without raising `NotFittedError`, so put the model into a fitted state by actually calling `.fit(...)` on it (which is what makes sklearn's `check_is_fitted` pass) rather than presetting `coef_`/`intercept_` on an unfitted estimator or using a final pipeline step that has no `.predict()`. Log it with mlflow.sklearn.log_model inside that buoy's active run (so it is a proper MLflow logged model tied to the run, not a raw artifact), then register that logged model as a version of a single registered model named buoy_drift_correction, assign the buoy's id as the registry alias (so models:/buoy_drift_correction@<buoy_id> resolves to that version via get_model_version_by_alias), and tag that registered model version with validation_status=accepted using MlflowClient.set_model_version_tag. Do NOT register or alias rejected buoys. In summary.json also include an "accepted" list and a "rejected" list of buoy ids and an "n_accepted" count in the fleet object.
