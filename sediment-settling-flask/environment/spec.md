# Settling-Column Inference — Data & Method Specification (v1)

This document is the contract for the sediment settling-column analysis pipeline. The analysis
targets **experiment_id 7** (label `SC-2207`). All outputs are written under `/app/output/`.

## 1. Experiment database: `/app/experiments.db` (SQLite)

`experiments(experiment_id, label, column_height_cm, fluid_viscosity_pa_s, fluid_density_kg_m3,
particle_density_kg_m3, temperature_c, sensor_id)` and
`sensors(sensor_id, model, units, raw_scale, raw_offset)`, joined on `sensor_id`. This database holds
inputs only — experiment metadata and per-sensor calibration constants.

## 2. Observation API (`http://127.0.0.1:8000`, already running)

- `GET /health` → `{"status": "ok"}`.
- `GET /experiments` → `{"experiment_ids": [...]}`.
- `GET /experiments/<id>/observations?page=N` → a page of **raw** sensor readings:
  `{"experiment_id", "page", "page_size", "total", "next", "observations": [{"t_ms", "raw_level"}, ...]}`.
  Results are **paginated** (`page_size` = 25); `next` is the next page number or `null` on the last
  page. To get the full series you must follow `next` until it is `null`.

Raw readings are converted to physical units with the experiment's sensor calibration:
`height_cm = raw_level * raw_scale + raw_offset` and `time_s = t_ms / 1000`.

## 3. Settling model and fit

Interface height follows a compression-settling decay, with `H0 = column_height_cm` known from the
metadata:

```
H(t) = h_inf + (H0 - h_inf) * exp(-k * t)
```

Fit the two free parameters `(h_inf, k)` to the converted `(time_s, height_cm)` series by nonlinear
least squares (`scipy.optimize.curve_fit`, default Levenberg–Marquardt). Report:

- **Parameter estimates**: `h_inf_cm`, `k_per_s`.
- **95% confidence half-widths**: `1.96 * sqrt(diag(pcov))` for each parameter
  (`h_inf_cm_ci95`, `k_per_s_ci95`).
- **Derived quantities**:
  - initial settling velocity `v0_cm_per_s = k * (H0 - h_inf)`;
  - Stokes-law effective particle diameter, in micrometres,
    `effective_diameter_um = sqrt( 18 * mu * (v0_cm_per_s / 100) / ( g * (rho_p - rho_f) ) ) * 1e6`,
    with `mu = fluid_viscosity_pa_s`, `rho_p = particle_density_kg_m3`, `rho_f = fluid_density_kg_m3`,
    and `g = 9.81`.
- **Residual metrics** against the fitted curve: `rmse_cm`, coefficient of determination `r2`, and
  `n_obs` (number of observations fitted).

## 4. Output artifacts (all under `/app/output/`)

**`metadata.json`** — a JSON object with the target experiment's metadata and calibration:
`experiment_id, label, column_height_cm, fluid_viscosity_pa_s, fluid_density_kg_m3,
particle_density_kg_m3, temperature_c, raw_scale, raw_offset`.

**`observations.csv`** — header `time_s,height_cm`, one row per observation (converted to physical
units), sorted by ascending `time_s`.

**`report.json`**:
```json
{
  "experiment_id": 7,
  "model": "H(t)=h_inf+(H0-h_inf)*exp(-k*t)",
  "parameters": {"h_inf_cm": <float>, "k_per_s": <float>},
  "ci95": {"h_inf_cm": <float>, "k_per_s": <float>},
  "derived": {"v0_cm_per_s": <float>, "effective_diameter_um": <float>},
  "residuals": {"rmse_cm": <float>, "r2": <float>, "n_obs": <int>}
}
```

**`report.csv`** — header `quantity,value`, one row for each of: `h_inf_cm`, `k_per_s`,
`h_inf_cm_ci95`, `k_per_s_ci95`, `v0_cm_per_s`, `effective_diameter_um`, `rmse_cm`, `r2`, `n_obs`.
