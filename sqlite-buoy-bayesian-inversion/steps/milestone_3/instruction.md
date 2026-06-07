Finally, add an `invert` subcommand so `/app/buoy_calibrate invert` runs the Bayesian inversion for each calibrated buoy. The cleaned residual follows a change-point drift model:

    residual(t) = offset + drift * t + drift_change * max(0, t - t_changepoint) + noise

where t is elapsed days since the mission epoch and t_changepoint is the protocol's drift changepoint expressed in elapsed days. The noise is independent zero-mean Gaussian but heteroscedastic: observation i has its own known standard deviation (the measurement_std column), so the inversion must be weighted by the inverse of each observation's variance rather than treating the noise as constant. Pick each buoy's priors by its sensor type and put the protocol's independent Gaussian priors on the three parameters (offset, drift, drift_change). Report the conjugate Gaussian posterior — its mean and standard deviation for each parameter and a central 95% credible interval. No sampling is needed; the posterior is available in closed form for this weighted linear-Gaussian model: with design matrix `X` whose rows are `[1, t, max(0, t - t_changepoint)]`, weights `W = diag(1/std^2)`, prior mean `m0` and prior covariance `S0 = diag(std_prior^2)`, the posterior covariance is `Sn = (S0^-1 + X^T W X)^-1` and the posterior mean is `mn = Sn (S0^-1 m0 + X^T W r)`; the parameter standard deviations are the square roots of the diagonal of `Sn` and the 95% interval is `mean ± 1.959963984540054 * std`.

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

`changepoint_t_days` is `t_changepoint` in elapsed days. `rmse_residual` is the root-mean-square residual before correction, and `corrected_rmse` is the root-mean-square of the residual after subtracting the fitted `offset + drift*t + drift_change*hinge` term. Also write /app/artifacts/summary.json with a `"buoys"` list (one entry per calibrated buoy carrying at least its `buoy_id`, `sensor_type`, `status`, `n_observations`, `offset_mean`, `drift_mean`, `drift_change_mean`, and `corrected_rmse`), an `"accepted"` list and a `"rejected"` list of buoy ids, and a `"fleet"` object holding `"n_buoys"`, `"n_accepted"` and `"mean_corrected_rmse"` across the calibrated fleet.

Apply this acceptance gate: a buoy's calibration is accepted only if its drift_change is statistically resolved — its 95% credible interval for drift_change excludes zero — and is rejected otherwise.

For each accepted buoy, register its deployable drift-correction model in /app/artifacts/registry.json, a single JSON object of the form `{"models": {"<buoy_id>": {"offset": <float>, "drift": <float>, "drift_change": <float>, "changepoint_t_days": <float>, "sensor_type": "<string>"}}}`, using that buoy's posterior-mean offset, drift and drift_change. Do NOT register rejected buoys. Then make `/app/buoy_calibrate predict --buoy <buoy_id> --t <t_days> --hinge <hinge>` read registry.json and print the correction `offset + drift*t_days + drift_change*hinge` for that registered buoy (printing the value to stdout); it must exit with a non-zero status for a buoy that is not registered. This is the deployable model: querying it must reproduce the posterior-mean correction.
