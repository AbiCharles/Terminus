Finally, add an `invert` subcommand so `/app/buoy_calibrate invert` runs the Bayesian inversion for each calibrated buoy. The cleaned residual follows a multi-change-point drift model with the `K` changepoints from the protocol (`K = 4` for this mission):

    residual(t) = offset + drift * t + sum_{k=1..K} drift_change_k * max(0, t - cp_k) + noise

where t is elapsed days since the mission epoch and `cp_k` is the k-th drift changepoint in elapsed days. The noise is independent zero-mean Gaussian but heteroscedastic: observation i has its own known standard deviation (the measurement_std column), so the inversion must be weighted by the inverse of each observation's variance rather than treating the noise as constant. Pick each buoy's priors by its sensor type and put the protocol's independent Gaussian priors on the `K+2` parameters — the offset, the drift, and one drift change per changepoint (the single drift-change prior applies identically to every drift_change_k). Report the conjugate Gaussian posterior — its mean and standard deviation for each parameter and a central 95% credible interval. No sampling is needed; the posterior is available in closed form for this weighted linear-Gaussian model: with design matrix `X` whose rows are `[1, t, max(0, t - cp_1), ..., max(0, t - cp_K)]` (so `X` has `K+2` columns), weights `W = diag(1/std^2)`, prior mean `m0` and prior covariance `S0 = diag(std_prior^2)`, the posterior covariance is `Sn = (S0^-1 + X^T W X)^-1` and the posterior mean is `mn = Sn (S0^-1 m0 + X^T W r)`; the parameter standard deviations are the square roots of the diagonal of `Sn` and the 95% interval is `mean ± 1.959963984540054 * std`. Note that this is a general `(K+2)x(K+2)` linear system — you must solve/invert it for arbitrary dimension, not with a hand-coded 3x3 formula.

Write /app/artifacts/<buoy_id>/posterior.json with this shape (the `drift_changes` arrays carry one entry per changepoint, in the same order as the protocol's changepoints):

```json
{
  "buoy_id": "<string>",
  "sensor_type": "<string>",
  "n_observations": <int>,
  "changepoints_t_days": [<float>, ...],
  "posterior": {
    "offset": {"mean": <float>, "std": <float>},
    "drift": {"mean": <float>, "std": <float>},
    "drift_changes": [{"mean": <float>, "std": <float>}, ...]
  },
  "credible_interval_95": {
    "offset": [<float>, <float>],
    "drift": [<float>, <float>],
    "drift_changes": [[<float>, <float>], ...]
  },
  "calibration": {"rmse_residual": <float>, "corrected_rmse": <float>}
}
```

`changepoints_t_days` lists the `K` changepoints in elapsed days. `rmse_residual` is the root-mean-square residual before correction, and `corrected_rmse` is the root-mean-square of the residual after subtracting the fitted `offset + drift*t + sum_k drift_change_k*max(0, t - cp_k)` term. Also write /app/artifacts/summary.json with a `"buoys"` list (one entry per calibrated buoy carrying at least its `buoy_id`, `sensor_type`, `status`, `n_observations`, `offset_mean`, `drift_mean`, `drift_change_means` (the list of posterior-mean drift changes), and `corrected_rmse`), an `"accepted"` list and a `"rejected"` list of buoy ids, and a `"fleet"` object holding `"n_buoys"` (the number of calibrated buoys), `"n_accepted"` (how many passed the acceptance gate), and `"mean_corrected_rmse"` — the mean of `corrected_rmse` over **all** calibrated buoys (every included buoy, whether accepted or rejected by the gate), not only the accepted ones.

Apply this acceptance gate: a buoy's calibration is accepted only if its drift change is statistically resolved at **at least one** changepoint — i.e. the 95% credible interval of some drift_change_k excludes zero — and is rejected otherwise.

For each accepted buoy, register its deployable drift-correction model in /app/artifacts/registry.json, a single JSON object of the form `{"models": {"<buoy_id>": {"offset": <float>, "drift": <float>, "drift_changes": [<float>, ...], "changepoints_t_days": [<float>, ...], "sensor_type": "<string>"}}}`, using that buoy's posterior-mean offset, drift and drift_changes. Do NOT register rejected buoys. Then make `/app/buoy_calibrate predict --buoy <buoy_id> --t <t_days>` read registry.json and print the correction `offset + drift*t_days + sum_k drift_change_k*max(0, t_days - cp_k)` for that registered buoy (computing the hinges from the registered changepoints, printing the value to stdout); it must exit with a non-zero status for a buoy that is not registered. This is the deployable model: querying it must reproduce the posterior-mean correction.
