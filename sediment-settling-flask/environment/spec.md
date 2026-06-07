# Settling-Column Sedimentation Analysis — Technical Specification

Binding contract for the pipeline. All paths, schemas, the conversion, the fit
configuration, and the derived formulas are normative: the verifier reads/writes
the same artifacts and recomputes the same quantities. **All work targets
`experiment_id = 1`.** Outputs go under `/app/output/`.

## 1. Inputs

### SQLite metadata — `/app/experiments.db`
Table `experiments(experiment_id, label, column_height_cm, fluid_viscosity_pa_s,
fluid_density_kg_m3, particle_density_kg_m3, temperature_c, sensor_id)` and table
`sensors(sensor_id, raw_scale, raw_offset, units)`. Each experiment references one
sensor whose calibration converts raw readings to physical units.

### Observations API — `http://127.0.0.1:8000`
A local Flask service (source under `/app/api/`). If it is not already running,
start it with `bash /app/start_api.sh`. Endpoints:
- `GET /health` → `{"status": "ok"}`
- `GET /experiments` → `{"experiment_ids": [...]}`
- `GET /experiments/<id>/observations?page=<n>` → a page of raw readings:
  `{"experiment_id", "page", "page_size", "total", "total_pages",
    "observations": [{"seq", "t_ms", "raw_level", "valid"}, ...]}`

Readings are **paginated** (`page_size = 20`, pages numbered from 1); you must read
every page to obtain all `total` observations. Each reading is **raw**: `t_ms` is
milliseconds and `raw_level` is an uncalibrated sensor value. A reading with
`valid = 0` is a sensor dropout and must be discarded.

## 2. Milestone 1 — `/app/output/metadata.json`

A JSON object for experiment 1 joining the experiment row with its sensor
calibration, with exactly these keys:

```json
{
  "experiment_id": <int>, "label": <str>, "column_height_cm": <float>,
  "fluid_viscosity_pa_s": <float>, "fluid_density_kg_m3": <float>,
  "particle_density_kg_m3": <float>, "temperature_c": <float>,
  "sensor_id": <int>, "raw_scale": <float>, "raw_offset": <float>
}
```

## 3. Milestone 2 — `/app/output/observations.csv`

Fetch **all pages** of experiment 1's observations, drop every reading with
`valid = 0`, convert the rest to physical units, and write a CSV with header
`time_s,height_cm` sorted by ascending `time_s`:

```
time_s   = t_ms / 1000
height_cm = raw_level * raw_scale + raw_offset      (raw_scale, raw_offset from the sensor)
```

One row per valid observation.

## 4. Milestone 3 — `/app/output/report.json`

Fit the interface-height settling model to the milestone-2 observations
`(time_s, height_cm)`:

```
H(t) = H_inf + (H0 - H_inf) * exp(-k * t)
```

`H0 = column_height_cm` is known and fixed; fit the two parameters `H_inf` and `k`
with `scipy.optimize.curve_fit`, initial guess `p0 = [H0 / 2, 0.01]` and
`maxfev = 10000` (default method). The 95% confidence half-widths are
`1.96 * sqrt(diag(pcov))`.

Derived quantities:
```
initial_velocity_cm_s = k * (H0 - H_inf)
effective_diameter_um = sqrt( 18 * mu * (initial_velocity_cm_s / 100) / (g * (rho_p - rho_f)) ) * 1e6
        with g = 9.81, mu = fluid_viscosity_pa_s, rho_p = particle_density_kg_m3, rho_f = fluid_density_kg_m3
```

Residual metrics on the fitted points: `rmse = sqrt(mean(residual^2))`,
`r2 = 1 - SS_res / SS_tot`, `n_obs` = number of fitted observations.

Write `/app/output/report.json` with exactly these keys:

```json
{
  "experiment_id": <int>,
  "h_inf_cm": <float>, "k_per_s": <float>,
  "h_inf_ci95": <float>, "k_ci95": <float>,
  "initial_velocity_cm_s": <float>, "effective_diameter_um": <float>,
  "rmse": <float>, "r2": <float>, "n_obs": <int>
}
```
