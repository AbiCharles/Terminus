# Settling-Column Inference — Data & Method Specification (v2)

This document is the contract for the sediment settling-column analysis pipeline. The analysis
targets **experiment_id 7** (label `SC-2207`). All outputs are written under `/app/output/`.

## 1. Experiment database: `/app/experiments.db` (SQLite)

`experiments(experiment_id, label, column_height_cm, fluid_viscosity_pa_s, fluid_density_kg_m3,
particle_density_kg_m3, temperature_c, sensor_id)` joined to `sensors(sensor_id, model, units,
raw_scale, raw_offset)` on `sensor_id`. Inputs only — metadata and per-sensor calibration constants.

## 2. Observation API (`http://127.0.0.1:8000`, already running)

The timing and level streams are served by **two separate paginated endpoints** and must be joined
on `seq`:

- `GET /experiments/<id>/timestamps?page=N` →
  `{"experiment_id","page","page_size","total","next","timestamps":[{"seq","t_ms"}, ...]}`.
- `GET /experiments/<id>/levels?page=N` →
  `{"experiment_id","page","page_size","total","next","levels":[{"seq","raw_level"}, ...]}`.
- `GET /experiments` → `{"experiment_ids":[...]}`; `GET /health` → `{"status":"ok"}`.

Both are paginated (`page_size` = 25; follow `next` until it is `null`). **The `levels` stream is
returned in sensor acquisition order, NOT sorted by `seq`** — you must join the two streams on `seq`
(not by position) to reconstruct each observation. An observation's physical values are
`time_s = t_ms / 1000` and `height_cm = raw_level * raw_scale + raw_offset`.

## 3. Settling model and fit

The interface descends in two phases with an unknown breakpoint `t_c` (continuous at `t_c`), with
`H0 = column_height_cm` known:

```
H(t) = H0 - v1 * t                                   for t <= t_c        (free settling)
H(t) = h_inf + (H0 - v1*t_c - h_inf) * exp(-k*(t-t_c))   for t >  t_c     (compression)
```

Estimate `(t_c, v1, h_inf, k)` as follows, on the converted, time-sorted `(time_s, height_cm)` series:

1. **Candidate breakpoints**: each distinct `time_s` value `t_c` that has at least **5** observations
   with `time_s < t_c` and at least **5** with `time_s >= t_c`.
2. For each candidate `t_c`, fit `(v1, h_inf, k)` to the full series with
   `scipy.optimize.curve_fit` (the piecewise model above, continuity enforced via
   `H0 - v1*t_c`), using `p0 = [1.0, min(height_cm), 0.05]` and `maxfev = 10000`; record the sum of
   squared residuals.
3. Choose the candidate `t_c` with the **smallest** SSE; its fit provides the estimates and the
   covariance `pcov`.

Report:
- **breakpoint** `t_c_s`.
- **Parameters**: `v1_cm_per_s`, `h_inf_cm`, `k_per_s`.
- **95% CI half-widths**: `1.96 * sqrt(diag(pcov))` for each parameter.
- **Derived**: Stokes-law effective particle diameter in micrometres from the initial settling
  velocity `v1`:
  `effective_diameter_um = sqrt( 18 * mu * (v1_cm_per_s / 100) / ( g * (rho_p - rho_f) ) ) * 1e6`,
  with `mu = fluid_viscosity_pa_s`, `rho_p = particle_density_kg_m3`, `rho_f = fluid_density_kg_m3`,
  `g = 9.81`.
- **Residuals** on the chosen fit: `rmse_cm`, `r2`, `n_obs`.

## 4. Output artifacts (all under `/app/output/`)

**`metadata.json`** — JSON object: `experiment_id, label, column_height_cm, fluid_viscosity_pa_s,
fluid_density_kg_m3, particle_density_kg_m3, temperature_c, raw_scale, raw_offset`.

**`observations.csv`** — header `time_s,height_cm`, one row per observation (joined + converted),
sorted by ascending `time_s`.

**`report.json`**:
```json
{
  "experiment_id": 7,
  "breakpoint": {"t_c_s": <float>},
  "parameters": {"v1_cm_per_s": <float>, "h_inf_cm": <float>, "k_per_s": <float>},
  "ci95": {"v1_cm_per_s": <float>, "h_inf_cm": <float>, "k_per_s": <float>},
  "derived": {"effective_diameter_um": <float>},
  "residuals": {"rmse_cm": <float>, "r2": <float>, "n_obs": <int>}
}
```

**`report.csv`** — header `quantity,value`, one row for each of: `t_c_s`, `v1_cm_per_s`, `h_inf_cm`,
`k_per_s`, `v1_cm_per_s_ci95`, `h_inf_cm_ci95`, `k_per_s_ci95`, `effective_diameter_um`, `rmse_cm`,
`r2`, `n_obs`.
