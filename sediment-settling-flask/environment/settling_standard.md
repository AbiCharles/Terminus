# Standard Practice for Settling-Column Sedimentation Analysis

**Designation:** MSL-SP-118
**Revision:** C (effective 2026-01-01)
**Supersedes:** Revision A (2019-03-01) and Revision B (2022-06-15)
**Issuing body:** Meridian Sedimentation Laboratory — Methods Committee

> **Precedence.** Only the requirements stated in the governing sections of **this Revision C**
> document are binding. Values appearing in the revision history (§12), the worked example (§10),
> and the appendices are provided for context, illustration, or historical traceability and are
> **not** the operative configuration. Several of them are **superseded** Revision A/B settings or
> pertain to a *different* experiment; where any such value differs from the governing analysis
> method in §9, §9 controls.

## Foreword

This practice was developed by the Methods Committee of the Meridian Sedimentation Laboratory (MSL) to standardise the reduction of settling-column interface-height records into estimated settling parameters. It consolidates two decades of laboratory experience with hindered- and compression-settling measurements and replaces the procedures previously circulated as internal memoranda MSL-IM-44 through MSL-IM-71.

The committee emphasises that this is a *practice* rather than a *test method*: it prescribes how an already-acquired interface-height series is to be analysed, not how the column experiment itself is to be run (that is covered by MSL-SP-090). Where a laboratory's local procedure differs from this practice, the differences shall be recorded in the analysis report and justified.

Revision C introduces three substantive changes relative to Revision B: the breakpoint search now requires a larger minimum number of points on each side of a candidate transition; the optimiser iteration budget has been increased; and per-sensor calibration is now mandatory, withdrawing the former laboratory-wide calibration constant. Operators migrating analyses from Revision A or B should read §12 carefully, as several historical defaults are now superseded.

Throughout this document, numerical values printed in the governing sections (§5-§9) are binding. Numerical values printed elsewhere — in the foreword, the worked examples, the inter-laboratory study, the uncertainty budget, or any appendix — are illustrative and must never be copied into an analysis configuration in place of the governing values.

## §1 Scope

This practice covers the reduction of settling-column interface-height time series into estimated settling parameters for a single experiment. It defines the analysis-method configuration that an operator must apply: the kinetic model, the parameter-initialisation and optimisation settings, the confidence-interval convention, the physical constants, and the reporting units. Per-experiment conditions and per-sensor calibration constants are **not** in this document; they are held in the laboratory database and are retrieved per experiment (see §5).

The practice applies to aqueous mineral suspensions analysed in vertical settling columns instrumented with a single optical interface-level probe. It does not cover centrifugal sedimentation, pipette analysis, hydrometer analysis, or laser-diffraction sizing; those methods are addressed by separate MSL practices and are referenced here only for context.

This practice does not purport to address all of the safety concerns, if any, associated with its use. It is the responsibility of the user of this practice to establish appropriate safety, health, and environmental practices and to determine the applicability of regulatory limitations prior to use. See §23 for a non-exhaustive summary of laboratory hazards.

## §2 Referenced Documents

The following documents are referenced. Unless a specific revision is cited, the current revision applies. None of these referenced documents contains operative analysis values for this practice; values are taken only from §5-§9 of this document and the laboratory database.

- **MSL-SP-090** — Standard Method for Conducting Settling-Column Tests.
- **MSL-SP-101** — Sensor Calibration Records and Traceability.
- **MSL-SP-118** — this practice.
- **MSL-SP-204** — Column Apparatus Maintenance and Cleaning.
- **MSL-DB-3** — Experiment Registry Database Schema.
- **MSL-QA-12** — Quality Assurance for Sedimentation Analyses.
- **ISO 13317-1** — Determination of particle size distribution — Gravitational liquid sedimentation.
- **ASTM D422** — Standard Test Method for Particle-Size Analysis of Soils (withdrawn, cited for context).
- **ISO/IEC Guide 98-3** — Uncertainty of measurement (GUM).

## §3 Terminology

For the purposes of this practice, the following definitions apply.

- *interface height* — the elevation of the clear-supernatant/suspension boundary above the column base, in centimetres.
- *free-settling phase* — the initial, approximately linear descent of the interface, during which particles settle at a hindered but roughly constant velocity.
- *compression phase* — the later regime in which the settled bed consolidates and the interface approaches its final height asymptotically.
- *breakpoint* — the transition time `t_c` separating the free-settling and compression phases.
- *initial settling velocity* — the magnitude `v1` of the interface descent rate during the free-settling phase, in centimetres per second.
- *final bed height* — the asymptotic interface height `h_inf` reached after full compression.
- *compression rate constant* — the first-order rate constant `k` governing the exponential approach to the final bed height, in reciprocal seconds.
- *effective diameter* — the Stokes-equivalent spherical particle diameter inferred from the initial settling velocity, reported in micrometres.
- *raw level* — the dimensionless integer reported by the optical probe prior to calibration.
- *calibration constants* — the per-sensor `raw_scale` and `raw_offset` that convert a raw level to an interface height in centimetres.
- *sequence index* — the monotonic acquisition counter `seq` attached to each sample, used to align the timing and level channels.
- *coverage factor* — the multiplier applied to a standard uncertainty to obtain an expanded uncertainty at a stated level of confidence.

## §4 Significance and Use

Settling-column analysis provides estimates of bulk settling behaviour that are used in the design of clarifiers, thickeners, and tailings-management facilities, and in the characterisation of natural sediment transport. The parameters estimated by this practice — the initial settling velocity, the final bed height, the compression rate constant, and the derived effective diameter — feed directly into those design and characterisation workflows.

Because downstream design decisions depend on the estimated parameters, it is essential that the analysis configuration be applied exactly as specified. Small changes to the kinetic model, the breakpoint search rule, or the confidence-interval convention can shift the reported parameters and their stated uncertainties enough to affect an engineering decision. For this reason §9 fixes every element of the analysis configuration, and operators are cautioned against substituting values from older revisions or from illustrative material elsewhere in this document.

## §5 Calibration and Per-Experiment Conditions

Per-sensor calibration constants (`raw_scale`, `raw_offset`) and per-experiment conditions (column height, fluid viscosity, fluid density, particle density, temperature, assigned sensor) are recorded in the laboratory database and must be read from it for the experiment under analysis — they are not reproduced here. Physical height is `raw_scale * raw_level + raw_offset` in centimetres. (Revision A used a single laboratory-wide calibration of `raw_scale = 0.0100`, `raw_offset = 0.0`; this global calibration is **withdrawn** — always use the per-sensor record.)

The calibration record for each probe is established under MSL-SP-101 and is traceable to the laboratory's reference length standard. A representative (non-binding) listing of probe records is given in §17 for context; the authoritative constants for the experiment under analysis are those in the database, not the listing.

## §6 Test Procedure (summary)

A specimen is dispersed, the column is filled to its marked height, and the interface elevation is logged until the bed stabilises. The acquisition order of level samples is **not** guaranteed to be monotonic in sequence index; each level sample carries its sequence number for alignment with the timing channel. The full experimental procedure is given in MSL-SP-090; only the analysis of the resulting record is within the scope of this practice.

## §7 Experiment Registry

The current registry holds twelve experiments (labels `SC-2201` … `SC-2212`). **The analysis described by this practice is to be applied to experiment 7 (label `SC-2207`).** Other registry entries are listed for completeness and must not be analysed in its place.

| id | label | suspension | column height | fluid | notes |
|----|-------|------------|---------------|-------|-------|
| 1 | SC-2201 | kaolinite slurry, 12 g/L | 40.0 cm | deionised water at 20 °C | baseline turbidity run; sensor CP-08 |
| 2 | SC-2202 | montmorillonite, 8 g/L | 38.5 cm | 0.01 M NaCl | swelling-clay control |
| 3 | SC-2203 | silica flour, 25 g/L | 45.0 cm | deionised water at 25 °C | coarse fraction |
| 4 | SC-2204 | kaolinite slurry, 15 g/L | 42.0 cm | deionised water at 22 °C | subject of the §10 worked example |
| 5 | SC-2205 | illite, 10 g/L | 41.0 cm | 0.05 M CaCl2 | flocculated regime |
| 6 | SC-2206 | calcium carbonate, 30 g/L | 44.0 cm | tap water at 18 °C | high-density mineral |
| 7 | SC-2207 | kaolinite slurry, 14 g/L | 42.0 cm | deionised water at 21 °C | **the experiment governed by this analysis** |
| 8 | SC-2208 | bentonite, 6 g/L | 39.0 cm | 0.10 M NaCl | gel-forming; slow compression |
| 9 | SC-2209 | silt mixture, 20 g/L | 43.0 cm | deionised water at 23 °C | natural sediment |
| 10 | SC-2210 | alumina, 18 g/L | 40.5 cm | deionised water at 20 °C | narrow size band |
| 11 | SC-2211 | fly ash, 22 g/L | 46.0 cm | 0.02 M NaCl | industrial residue |
| 12 | SC-2212 | kaolinite/silica blend, 16 g/L | 42.5 cm | deionised water at 24 °C | bimodal |

The column heights and fluid descriptions above are contextual; the authoritative per-experiment conditions used in the analysis are read from the database (§5), not from this table. The table is provided so an operator can confirm that experiment 7 corresponds to label `SC-2207`.

## §8 Units and Physical Constants

Times are recorded in milliseconds and shall be converted to **seconds** by dividing by **1000**.
Heights are in centimetres. The gravitational acceleration used in the Stokes relation (§9) shall be
taken as **g = 9.81 m/s²**. (A more precise standard-gravity value appears in Appendix A for unit
work; it is not used in this reduction.) The reported effective diameter shall be expressed in
**micrometres**.

## §9 Analysis Method (governing)

The interface-height series `H(t)` (in cm, versus time in s) for the experiment shall be reduced as
follows.

**9.1 Model.** Use the **two-phase** model with an unknown breakpoint `t_c`, continuous at `t_c`:

```
H(t) = H0 - v1*t                                  for t <= t_c     (free settling)
H(t) = h_inf + (H0 - v1*t_c - h_inf)*exp(-k*(t-t_c))   for t > t_c  (compression)
```

where `H0` is the experiment's column height. (Revision A specified a single-exponential model with
no breakpoint; that model is **superseded** and shall not be used.)

**9.2 Breakpoint search.** The candidate breakpoints are the distinct observation times that have at
least **5** observations on each side (strictly before, and at or after). For each candidate, fit the
free parameters and retain the candidate giving the smallest sum of squared residuals. (Revision B
required only **3** observations on each side; Revision C raised this to 5.)

**9.3 Fitting.** At each candidate breakpoint, estimate `(v1, h_inf, k)` by nonlinear least squares
(Levenberg–Marquardt) with initial guesses **v1 = 1.0 cm/s**, **k = 0.05 1/s**, and `h_inf` set to
the **minimum observed height**, and a maximum of **10000** function evaluations. (Revision A used a
function-evaluation cap of 5000; that limit is superseded.)

**9.4 Confidence intervals.** Report 95% confidence half-widths as **1.96 × the standard error** of
each fitted parameter (the square root of the corresponding diagonal element of the covariance
matrix). Although some operators adopt a coverage factor of 2.0, this practice fixes the 95%
multiplier at **1.96**; the 99% factor of 2.576 is not used here.

**9.5 Derived effective diameter.** From the initial settling velocity `v1`, compute the
Stokes-equivalent diameter
`d = sqrt( 18 * mu * (v1/100) / ( g * (rho_p - rho_f) ) ) * 1e6` micrometres, with `mu` the fluid
viscosity, `rho_p` the particle density, `rho_f` the fluid density, and `g` from §8.

## §10 Worked Example (illustrative only — different experiment)

For illustration on experiment `SC-2204` (not the subject of this analysis), an operator obtained a
breakpoint near 9 s with `v1 ≈ 0.5 cm/s`, `h_inf ≈ 11 cm`, and `k ≈ 0.10 1/s`, starting the optimiser
from `v1 = 0.5`, `k = 0.10`. **These example values pertain to a different experiment and different
starting guesses and must not be used as the configuration for the analysis required by §9.**
## §11 Reporting

Report the breakpoint, the three fitted parameters with their 95% confidence half-widths, the derived effective diameter, and the fit residual metrics (root-mean-square error in cm, coefficient of determination, and the number of observations fitted), in the artifact formats required by the task.

Each reported quantity shall be accompanied, in the laboratory archive copy, by the configuration values used to produce it, so that an auditor can confirm that the governing §9 configuration — and not a superseded or illustrative value — was applied. The machine-readable configuration object produced by the analysis serves this purpose.

## §12 Revision History (non-binding)

- **Revision A (2019):** single-exponential model; breakpoint not modelled; optimiser cap 5000;
  laboratory-wide calibration `raw_scale = 0.0100`; confidence intervals reported at a coverage
  factor of 2.0; initial guesses `v1 = 0.5 cm/s`, `k = 0.10 1/s`.
- **Revision B (2022):** introduced the two-phase model; breakpoint search required ≥3 points per
  side; retained the 5000 evaluation cap; retained the coverage factor 2.0; initial guesses
  unchanged from Revision A.
- **Revision C (2026, current):** breakpoint search requires ≥5 points per side; optimiser cap
  10000; per-sensor calibration mandatory; confidence half-widths at the 1.96 multiplier; initial
  guesses `v1 = 1.0 cm/s`, `k = 0.05 1/s`. See §9 for the operative values.

The values listed under Revisions A and B above are recorded solely for traceability. They are **superseded** and must not be used in a Revision C analysis. Where this history and §9 disagree, §9 controls.

## §13 Quality Control and Acceptance Criteria

An analysis is acceptable under this practice when the following criteria are met: the fitted model explains at least 98% of the variance in the interface-height series (coefficient of determination ≥ 0.98); the root-mean-square residual does not exceed 0.5 cm; the chosen breakpoint lies strictly inside the observed time range with the required number of points on each side (§9.2); and the fitted initial settling velocity is positive.

These acceptance thresholds (0.98 and 0.5 cm) are quality gates on the *result*; they are not part of the fitting configuration and must not be confused with the optimiser settings of §9.3. A run that fails an acceptance criterion is repeated under MSL-SP-090, not re-fitted with altered settings.

Laboratories shall maintain control charts of the residual RMSE and the coefficient of determination across runs. A run whose RMSE exceeds the upper control limit of 0.5 cm, or whose coefficient of determination falls below 0.98, is flagged for review. Control limits are reviewed annually by the Methods Committee.

## §14 Measurement Uncertainty Budget

The combined standard uncertainty of each estimated parameter is obtained by propagating the contributions tabulated below through the fit. The dominant contributions are the level-sensor calibration uncertainty and the timing-channel quantisation. The expanded uncertainty reported to the client is the combined standard uncertainty multiplied by the coverage factor of §9.4.

| source | type | standard uncertainty | sensitivity | notes |
|--------|------|----------------------|-------------|-------|
| sensor calibration (scale) | B | 0.3% of height | ∂H/∂scale | from MSL-SP-101 record |
| sensor calibration (offset) | B | 0.02 cm | 1 | zero-point drift |
| timing quantisation | B | 0.5 ms / √3 | ∂t | 1 ms acquisition tick |
| interface definition | A | 0.05 cm | 1 | operator repeatability |
| temperature (viscosity) | B | 0.2 °C | ∂μ/∂T | affects Stokes diameter |
| column verticality | B | 0.1% | geometric | alignment check |
| model adequacy | A | residual RMSE | — | lack-of-fit component |

The coverage factor used to expand the combined standard uncertainty to a 95% interval is fixed by §9.4 at 1.96. Some clients request a 99% interval; the corresponding factor of 2.576 is provided for reference only and is not used in the standard report. The older laboratory convention of a coverage factor of 2.0 (Revisions A and B) is superseded.

## §15 Alternate and Superseded Kinetic Models (non-binding)

For historical context and for comparison studies, three kinetic models have been used at this laboratory. Only the two-phase model of §9.1 is operative under Revision C.

**Single-exponential model (Revision A, superseded).** `H(t) = h_inf + (H0 - h_inf) * exp(-k*t)`, with no breakpoint. This model was found to bias the initial settling velocity low for flocculated suspensions and was replaced in Revision B. It must not be used under Revision C, even though it remains available in the analysis library for reproducing historical results.

**Power-law compression model (experimental).** `H(t) = h_inf + a * (t + t0)^(-b)`. Investigated in an inter-laboratory study (§19) but never adopted; parameters are not comparable to the two-phase model and shall not be reported under this practice.

**Two-phase model (Revision B/C, operative).** Defined in §9.1. Revision C retains the model form introduced in Revision B but tightens the breakpoint search (§9.2) and the optimiser budget (§9.3).

## §16 Optimiser Configuration Guidance (non-binding commentary)

The nonlinear least-squares fit of §9.3 is performed with a Levenberg–Marquardt optimiser. This section provides commentary on the configuration; the binding values are those in §9.3, not those recalled here for discussion.

Historically (Revisions A and B) the optimiser was capped at 5000 function evaluations, which occasionally produced non-convergence on long records. Revision C raises the cap to 10000; the §9.3 value governs. The initial guesses were likewise changed: Revisions A and B started the optimiser from `v1 = 0.5 cm/s` and `k = 0.10 1/s`, whereas Revision C starts from `v1 = 1.0 cm/s` and `k = 0.05 1/s` (§9.3). The final-bed-height parameter is initialised at the minimum observed height in all revisions.

Operators should not interpret the commentary in this section as configuration. If a value here differs from §9.3 — for example the superseded 5000-evaluation cap or the superseded 0.5 cm/s starting velocity — the §9.3 value is the one to use.

## §17 Sensor Calibration Records (representative, non-binding)

The following table lists representative probe calibration records maintained under MSL-SP-101. It is provided for context only; the calibration constants used in an analysis are those attached to the experiment's assigned sensor in the database (§5), not those in this table.

| model | raw_scale | raw_offset | ADC range | serial |
|-------|-----------|------------|-----------|--------|
| ColumnProbe CP-04 | 0.00500 | +0.10 | 0-1023 | CP04-7781 |
| ColumnProbe CP-06 | 0.00750 | +0.05 | 0-2047 | CP06-3120 |
| ColumnProbe CP-08 | 0.01000 | +0.00 | 0-4095 | CP08-9904 |
| ColumnProbe CP-08 | 0.00980 | +0.02 | 0-4095 | CP08-9911 |
| ColumnProbe CP-10 | 0.01250 | -0.05 | 0-4095 | CP10-2245 |
| ColumnProbe CP-10 | 0.01180 | +0.03 | 0-4095 | CP10-2251 |
| ColumnProbe CP-12 | 0.01500 | +0.10 | 0-8191 | CP12-6680 |
| ColumnProbe CP-12 | 0.01470 | +0.08 | 0-8191 | CP12-6692 |
| ColumnProbe CP-14 | 0.02000 | +0.00 | 0-8191 | CP14-0034 |
| ColumnProbe CP-14 | 0.01950 | +0.04 | 0-8191 | CP14-0041 |
| ColumnProbe CP-16 | 0.02500 | -0.10 | 0-16383 | CP16-5519 |
| ColumnProbe CP-16 | 0.02440 | +0.06 | 0-16383 | CP16-5527 |
| ColumnProbe CP-18 | 0.03000 | +0.00 | 0-16383 | CP18-7702 |
| ColumnProbe CP-18 | 0.02960 | +0.05 | 0-16383 | CP18-7719 |
| ColumnProbe CP-20 | 0.04000 | +0.10 | 0-32767 | CP20-1188 |
| ColumnProbe CP-20 | 0.03920 | +0.07 | 0-32767 | CP20-1196 |

Each probe is recalibrated every six months or after any disassembly. The withdrawn laboratory-wide constant (`raw_scale = 0.0100`, `raw_offset = 0.0`) appears in none of these records and must not be substituted for a per-sensor value.

## §18 Experiment Registry Details (non-binding)

This section expands the registry of §7 with the conditions recorded for each experiment at acquisition time, together with the acquisition narrative and the quality-control outcome. These values are contextual; the authoritative per-experiment conditions are read from the database (§5). The analysis required by this practice applies to experiment 7 only; every other entry is included for completeness and traceability, and several quote settings that are not the governing ones.

### SC-2201 (experiment 1)

Suspension: kaolinite slurry, 12 g/L. Nominal column height: 40.0 cm. Fluid: deionised water at 20 °C. Recorded temperature approximately 21 °C. Assigned probe: ColumnProbe CP-08 (serial CP08-9911). Baseline turbidity run; sensor cp-08.

Acquisition produced 197 interleaved samples over roughly 29 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2202 (experiment 2)

Suspension: montmorillonite, 8 g/L. Nominal column height: 38.5 cm. Fluid: 0.01 M NaCl. Recorded temperature approximately 24 °C. Assigned probe: ColumnProbe CP-12 (serial CP12-6680). Swelling-clay control.

Acquisition produced 214 interleaved samples over roughly 36 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2203 (experiment 3)

Suspension: silica flour, 25 g/L. Nominal column height: 45.0 cm. Fluid: deionised water at 25 °C. Recorded temperature approximately 19 °C. Assigned probe: ColumnProbe CP-14 (serial CP14-0041). Coarse fraction.

Acquisition produced 231 interleaved samples over roughly 25 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2204 (experiment 4)

Suspension: kaolinite slurry, 15 g/L. Nominal column height: 42.0 cm. Fluid: deionised water at 22 °C. Recorded temperature approximately 22 °C. Assigned probe: ColumnProbe CP-18 (serial CP18-7702). Subject of the §10 worked example.

Acquisition produced 248 interleaved samples over roughly 32 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

This experiment is the subject of the §10 worked example. The numbers quoted there (breakpoint near 9 s, `v1 ≈ 0.5 cm/s`, `k ≈ 0.10 1/s`) pertain to SC-2204 and to the illustrative starting guesses used there; they are not the configuration for experiment 7.

### SC-2205 (experiment 5)

Suspension: illite, 10 g/L. Nominal column height: 41.0 cm. Fluid: 0.05 M CaCl2. Recorded temperature approximately 25 °C. Assigned probe: ColumnProbe CP-20 (serial CP20-1196). Flocculated regime.

Acquisition produced 265 interleaved samples over roughly 39 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2206 (experiment 6)

Suspension: calcium carbonate, 30 g/L. Nominal column height: 44.0 cm. Fluid: tap water at 18 °C. Recorded temperature approximately 20 °C. Assigned probe: ColumnProbe CP-08 (serial CP08-9904). High-density mineral.

Acquisition produced 192 interleaved samples over roughly 28 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2207 (experiment 7)

Suspension: kaolinite slurry, 14 g/L. Nominal column height: 42.0 cm. Fluid: deionised water at 21 °C. Recorded temperature approximately 23 °C. Assigned probe: ColumnProbe CP-10 (serial CP10-2251). **the experiment governed by this analysis**.

Acquisition produced 209 interleaved samples over roughly 35 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

**This is the experiment analysed under this practice.** Apply the governing configuration of §8 and §9: the two-phase model, at least five points on each side of the breakpoint, initial guesses of 1.0 cm/s and 0.05 1/s with the final-bed-height parameter started at the minimum observed height, a 10000-evaluation optimiser cap, a 1.96 coverage factor, gravity of 9.81 m/s², milliseconds divided by 1000, and the effective diameter expressed in micrometres. Do not use the illustrative values from the §10 worked example (which concerns SC-2204) or any superseded value from the revision history (§12) or the deprecated-defaults appendix (B).

### SC-2208 (experiment 8)

Suspension: bentonite, 6 g/L. Nominal column height: 39.0 cm. Fluid: 0.10 M NaCl. Recorded temperature approximately 18 °C. Assigned probe: ColumnProbe CP-14 (serial CP14-0034). Gel-forming; slow compression.

Acquisition produced 226 interleaved samples over roughly 24 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2209 (experiment 9)

Suspension: silt mixture, 20 g/L. Nominal column height: 43.0 cm. Fluid: deionised water at 23 °C. Recorded temperature approximately 21 °C. Assigned probe: ColumnProbe CP-16 (serial CP16-5527). Natural sediment.

Acquisition produced 243 interleaved samples over roughly 31 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2210 (experiment 10)

Suspension: alumina, 18 g/L. Nominal column height: 40.5 cm. Fluid: deionised water at 20 °C. Recorded temperature approximately 24 °C. Assigned probe: ColumnProbe CP-20 (serial CP20-1188). Narrow size band.

Acquisition produced 260 interleaved samples over roughly 38 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2211 (experiment 11)

Suspension: fly ash, 22 g/L. Nominal column height: 46.0 cm. Fluid: 0.02 M NaCl. Recorded temperature approximately 19 °C. Assigned probe: ColumnProbe CP-06 (serial CP06-3120). Industrial residue.

Acquisition produced 187 interleaved samples over roughly 27 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

### SC-2212 (experiment 12)

Suspension: kaolinite/silica blend, 16 g/L. Nominal column height: 42.5 cm. Fluid: deionised water at 24 °C. Recorded temperature approximately 22 °C. Assigned probe: ColumnProbe CP-10 (serial CP10-2245). Bimodal.

Acquisition produced 204 interleaved samples over roughly 34 minutes. As with every record under this practice, the level channel was stored in sensor acquisition order rather than sorted by sequence index, so the timing and level channels must be realigned by sequence index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.

Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide constant) was applied when converting raw levels to heights.

## §19 Inter-laboratory Comparison Study (non-binding)

In 2024 the Methods Committee organised an inter-laboratory comparison to assess the reproducibility of the two-phase analysis ahead of Revision C. Eight laboratories analysed a common set of interface-height records using their then-current configurations. The study is summarised here for context; none of its tabulated numbers is an operative configuration value.

| round | participating lab | model | min points/side | optimiser cap | coverage factor |
|-------|-------------------|-------|-----------------|---------------|-----------------|
| 1 | Meridian (lead) | two-phase | 3 | 5000 | 2.0 |
| 2 | Northvale Geotechnical | two-phase | 3 | 5000 | 2.0 |
| 3 | Coastal Sediments Inc. | single-exp | n/a | 2000 | 2.0 |
| 4 | Université du Littoral | two-phase | 4 | 8000 | 1.96 |
| 5 | Hokuriku Soil Mechanics | two-phase | 5 | 10000 | 1.96 |
| 6 | Cape Survey Labs | power-law | n/a | 4000 | 2.576 |
| 7 | Andes Hydrology Group | two-phase | 3 | 5000 | 2.0 |
| 8 | Baltic Particle Science | two-phase | 5 | 10000 | 1.96 |

The spread of configurations in the table above motivated the standardisation in Revision C. The committee adopted the configuration that gave the most reproducible initial settling velocity across laboratories: the two-phase model with at least five points on each side of the breakpoint, a 10000 evaluation cap, and a 1.96 coverage factor (§9). The other rows record what individual laboratories did at the time and are not to be emulated.

## §20 Data Acquisition and File Formats

The acquisition system records two channels per experiment. The timing channel stores, for each sequence index, the elapsed acquisition time in **milliseconds**. The level channel stores, for each sequence index, the raw integer probe reading. The two channels are exported independently and, in the laboratory's serving layer, are paginated; the level channel is not guaranteed to be ordered by sequence index.

Times are recorded in milliseconds. Older logbooks occasionally quoted elapsed times in minutes; the conversion 1 min = 60000 ms is provided for reading those logbooks and is not the conversion used in the analysis, which converts milliseconds to seconds per §8. Heights are derived from raw readings by the per-sensor calibration of §5.

## §21 Statistical Treatment of the Fit

Parameter standard errors are obtained from the square roots of the diagonal of the covariance matrix returned by the optimiser. The 95% confidence half-width for each parameter is the standard error multiplied by the coverage factor fixed in §9.4. For large samples the Gaussian factor 1.96 is appropriate and is the value adopted by this practice.

Several alternative conventions exist and are noted here only to forestall their accidental use. A coverage factor of 2.0 (a common rounding of 1.96) was used in Revisions A and B and is superseded. A factor of 2.576 corresponds to a 99% interval and is used only when a client explicitly requests 99% coverage. For very small samples a Student-t factor would be used in place of the Gaussian factor; settling-column records are large enough that this practice uses the Gaussian 1.96 in all cases.

The derived effective diameter inherits its uncertainty from the initial settling velocity through the Stokes relation of §9.5; its confidence interval is obtained by propagating the velocity standard error and is reported at the same 1.96 coverage factor.

## §22 Troubleshooting

- **Optimiser fails to converge.** Confirm the evaluation cap is set to the §9.3 value of 10000 rather than the superseded 5000; verify the initial guesses match §9.3; check that the interface series is monotonic non-increasing after realignment.
- **Breakpoint search returns no candidate.** The record may be too short to provide five points on each side of any interior time; acquire a longer record under MSL-SP-090. Do not relax the §9.2 minimum to the superseded value of three.
- **Negative fitted velocity.** Indicates a misaligned level channel; re-join the timing and level channels by sequence index rather than by position.
- **Effective diameter implausibly large.** Check that the gravitational constant is the §8 value of 9.81 m/s² and that viscosity and densities were read from the database in SI units.
- **Reported interval seems wide.** Confirm the coverage factor is 1.96 (§9.4) and not 2.576 (99%) or the superseded 2.0.

## §23 Safety

Mineral suspensions may contain respirable fines; prepare and disperse specimens in accordance with the laboratory's dust-control procedures. Saline and calcium-chloride fluids are mild irritants. Settling columns are tall glass or acrylic vessels; secure them against toppling. This section is a summary and does not replace the laboratory's safety documentation.

## §24 Apparatus Maintenance

Probe windows are cleaned between runs per MSL-SP-204. Columns are inspected for verticality before filling. The acquisition system clock is checked against a reference each quarter; a drift exceeding 0.1% requires recalibration of the timing channel. Maintenance records are retained for five years.

## §25 Validation Dataset Catalogue (non-binding)

During the development of Revision C the governing configuration was exercised on five replicate acquisitions of each registry experiment. The per-replicate fit summaries are catalogued here to document the reproducibility of the method. All numbers are outcomes of the analysis, not inputs to it; they are specific to the named experiment and replicate and are not configuration values.

### Catalogue — SC-2201

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 7.00 | 0.460 | 11.00 | 0.040 | 0.180 | 0.984 | 21.4 |
| 2 | 7.70 | 0.510 | 11.30 | 0.130 | 0.190 | 0.985 | 22.5 |
| 3 | 8.40 | 0.560 | 11.60 | 0.080 | 0.200 | 0.986 | 23.6 |
| 4 | 9.10 | 0.610 | 11.90 | 0.170 | 0.210 | 0.987 | 24.7 |
| 5 | 9.80 | 0.660 | 12.20 | 0.120 | 0.220 | 0.988 | 25.8 |
| 6 | 10.50 | 0.710 | 12.50 | 0.070 | 0.230 | 0.989 | 26.9 |
| 7 | 5.20 | 0.760 | 12.80 | 0.160 | 0.240 | 0.990 | 28.0 |
| 8 | 5.90 | 0.810 | 13.10 | 0.110 | 0.250 | 0.991 | 29.1 |
| 9 | 6.60 | 0.860 | 13.40 | 0.060 | 0.260 | 0.992 | 30.2 |
| 10 | 7.30 | 0.910 | 13.70 | 0.150 | 0.270 | 0.993 | 31.3 |
| 11 | 8.00 | 0.960 | 14.00 | 0.100 | 0.280 | 0.994 | 32.4 |
| 12 | 8.70 | 1.010 | 14.30 | 0.050 | 0.290 | 0.995 | 33.5 |
| 13 | 9.40 | 1.060 | 14.60 | 0.140 | 0.300 | 0.996 | 34.6 |
| 14 | 10.10 | 1.110 | 14.90 | 0.090 | 0.310 | 0.997 | 35.7 |
| 15 | 10.80 | 1.160 | 15.20 | 0.040 | 0.320 | 0.998 | 36.8 |
| 16 | 5.50 | 0.310 | 15.50 | 0.130 | 0.330 | 0.980 | 37.9 |
| 17 | 6.20 | 0.360 | 15.80 | 0.080 | 0.340 | 0.981 | 39.0 |
| 18 | 6.90 | 0.410 | 16.10 | 0.170 | 0.350 | 0.982 | 18.1 |

The eighteen replicates of SC-2201 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2202

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 8.30 | 0.570 | 12.70 | 0.090 | 0.250 | 0.987 | 23.7 |
| 2 | 9.00 | 0.620 | 13.00 | 0.040 | 0.260 | 0.988 | 24.8 |
| 3 | 9.70 | 0.670 | 13.30 | 0.130 | 0.270 | 0.989 | 25.9 |
| 4 | 10.40 | 0.720 | 13.60 | 0.080 | 0.280 | 0.990 | 27.0 |
| 5 | 5.10 | 0.770 | 13.90 | 0.170 | 0.290 | 0.991 | 28.1 |
| 6 | 5.80 | 0.820 | 14.20 | 0.120 | 0.300 | 0.992 | 29.2 |
| 7 | 6.50 | 0.870 | 14.50 | 0.070 | 0.310 | 0.993 | 30.3 |
| 8 | 7.20 | 0.920 | 14.80 | 0.160 | 0.320 | 0.994 | 31.4 |
| 9 | 7.90 | 0.970 | 15.10 | 0.110 | 0.330 | 0.995 | 32.5 |
| 10 | 8.60 | 1.020 | 15.40 | 0.060 | 0.340 | 0.996 | 33.6 |
| 11 | 9.30 | 1.070 | 15.70 | 0.150 | 0.350 | 0.997 | 34.7 |
| 12 | 10.00 | 1.120 | 16.00 | 0.100 | 0.360 | 0.998 | 35.8 |
| 13 | 10.70 | 1.170 | 16.30 | 0.050 | 0.370 | 0.980 | 36.9 |
| 14 | 5.40 | 0.320 | 16.60 | 0.140 | 0.380 | 0.981 | 38.0 |
| 15 | 6.10 | 0.370 | 16.90 | 0.090 | 0.390 | 0.982 | 39.1 |
| 16 | 6.80 | 0.420 | 9.20 | 0.040 | 0.400 | 0.983 | 18.2 |
| 17 | 7.50 | 0.470 | 9.50 | 0.130 | 0.410 | 0.984 | 19.3 |
| 18 | 8.20 | 0.520 | 9.80 | 0.080 | 0.420 | 0.985 | 20.4 |

The eighteen replicates of SC-2202 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2203

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 9.60 | 0.680 | 14.40 | 0.140 | 0.320 | 0.990 | 26.0 |
| 2 | 10.30 | 0.730 | 14.70 | 0.090 | 0.330 | 0.991 | 27.1 |
| 3 | 5.00 | 0.780 | 15.00 | 0.040 | 0.340 | 0.992 | 28.2 |
| 4 | 5.70 | 0.830 | 15.30 | 0.130 | 0.350 | 0.993 | 29.3 |
| 5 | 6.40 | 0.880 | 15.60 | 0.080 | 0.360 | 0.994 | 30.4 |
| 6 | 7.10 | 0.930 | 15.90 | 0.170 | 0.370 | 0.995 | 31.5 |
| 7 | 7.80 | 0.980 | 16.20 | 0.120 | 0.380 | 0.996 | 32.6 |
| 8 | 8.50 | 1.030 | 16.50 | 0.070 | 0.390 | 0.997 | 33.7 |
| 9 | 9.20 | 1.080 | 16.80 | 0.160 | 0.400 | 0.998 | 34.8 |
| 10 | 9.90 | 1.130 | 9.10 | 0.110 | 0.410 | 0.980 | 35.9 |
| 11 | 10.60 | 1.180 | 9.40 | 0.060 | 0.420 | 0.981 | 37.0 |
| 12 | 5.30 | 0.330 | 9.70 | 0.150 | 0.430 | 0.982 | 38.1 |
| 13 | 6.00 | 0.380 | 10.00 | 0.100 | 0.440 | 0.983 | 39.2 |
| 14 | 6.70 | 0.430 | 10.30 | 0.050 | 0.100 | 0.984 | 18.3 |
| 15 | 7.40 | 0.480 | 10.60 | 0.140 | 0.110 | 0.985 | 19.4 |
| 16 | 8.10 | 0.530 | 10.90 | 0.090 | 0.120 | 0.986 | 20.5 |
| 17 | 8.80 | 0.580 | 11.20 | 0.040 | 0.130 | 0.987 | 21.6 |
| 18 | 9.50 | 0.630 | 11.50 | 0.130 | 0.140 | 0.988 | 22.7 |

The eighteen replicates of SC-2203 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2204

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 10.90 | 0.790 | 16.10 | 0.050 | 0.390 | 0.993 | 28.3 |
| 2 | 5.60 | 0.840 | 16.40 | 0.140 | 0.400 | 0.994 | 29.4 |
| 3 | 6.30 | 0.890 | 16.70 | 0.090 | 0.410 | 0.995 | 30.5 |
| 4 | 7.00 | 0.940 | 9.00 | 0.040 | 0.420 | 0.996 | 31.6 |
| 5 | 7.70 | 0.990 | 9.30 | 0.130 | 0.430 | 0.997 | 32.7 |
| 6 | 8.40 | 1.040 | 9.60 | 0.080 | 0.440 | 0.998 | 33.8 |
| 7 | 9.10 | 1.090 | 9.90 | 0.170 | 0.100 | 0.980 | 34.9 |
| 8 | 9.80 | 1.140 | 10.20 | 0.120 | 0.110 | 0.981 | 36.0 |
| 9 | 10.50 | 1.190 | 10.50 | 0.070 | 0.120 | 0.982 | 37.1 |
| 10 | 5.20 | 0.340 | 10.80 | 0.160 | 0.130 | 0.983 | 38.2 |
| 11 | 5.90 | 0.390 | 11.10 | 0.110 | 0.140 | 0.984 | 39.3 |
| 12 | 6.60 | 0.440 | 11.40 | 0.060 | 0.150 | 0.985 | 18.4 |
| 13 | 7.30 | 0.490 | 11.70 | 0.150 | 0.160 | 0.986 | 19.5 |
| 14 | 8.00 | 0.540 | 12.00 | 0.100 | 0.170 | 0.987 | 20.6 |
| 15 | 8.70 | 0.590 | 12.30 | 0.050 | 0.180 | 0.988 | 21.7 |
| 16 | 9.40 | 0.640 | 12.60 | 0.140 | 0.190 | 0.989 | 22.8 |
| 17 | 10.10 | 0.690 | 12.90 | 0.090 | 0.200 | 0.990 | 23.9 |
| 18 | 10.80 | 0.740 | 13.20 | 0.040 | 0.210 | 0.991 | 25.0 |

The eighteen replicates of SC-2204 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2205

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 6.20 | 0.900 | 9.80 | 0.100 | 0.110 | 0.996 | 30.6 |
| 2 | 6.90 | 0.950 | 10.10 | 0.050 | 0.120 | 0.997 | 31.7 |
| 3 | 7.60 | 1.000 | 10.40 | 0.140 | 0.130 | 0.998 | 32.8 |
| 4 | 8.30 | 1.050 | 10.70 | 0.090 | 0.140 | 0.980 | 33.9 |
| 5 | 9.00 | 1.100 | 11.00 | 0.040 | 0.150 | 0.981 | 35.0 |
| 6 | 9.70 | 1.150 | 11.30 | 0.130 | 0.160 | 0.982 | 36.1 |
| 7 | 10.40 | 0.300 | 11.60 | 0.080 | 0.170 | 0.983 | 37.2 |
| 8 | 5.10 | 0.350 | 11.90 | 0.170 | 0.180 | 0.984 | 38.3 |
| 9 | 5.80 | 0.400 | 12.20 | 0.120 | 0.190 | 0.985 | 39.4 |
| 10 | 6.50 | 0.450 | 12.50 | 0.070 | 0.200 | 0.986 | 18.5 |
| 11 | 7.20 | 0.500 | 12.80 | 0.160 | 0.210 | 0.987 | 19.6 |
| 12 | 7.90 | 0.550 | 13.10 | 0.110 | 0.220 | 0.988 | 20.7 |
| 13 | 8.60 | 0.600 | 13.40 | 0.060 | 0.230 | 0.989 | 21.8 |
| 14 | 9.30 | 0.650 | 13.70 | 0.150 | 0.240 | 0.990 | 22.9 |
| 15 | 10.00 | 0.700 | 14.00 | 0.100 | 0.250 | 0.991 | 24.0 |
| 16 | 10.70 | 0.750 | 14.30 | 0.050 | 0.260 | 0.992 | 25.1 |
| 17 | 5.40 | 0.800 | 14.60 | 0.140 | 0.270 | 0.993 | 26.2 |
| 18 | 6.10 | 0.850 | 14.90 | 0.090 | 0.280 | 0.994 | 27.3 |

The eighteen replicates of SC-2205 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2206

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 7.50 | 1.010 | 11.50 | 0.150 | 0.180 | 0.980 | 32.9 |
| 2 | 8.20 | 1.060 | 11.80 | 0.100 | 0.190 | 0.981 | 34.0 |
| 3 | 8.90 | 1.110 | 12.10 | 0.050 | 0.200 | 0.982 | 35.1 |
| 4 | 9.60 | 1.160 | 12.40 | 0.140 | 0.210 | 0.983 | 36.2 |
| 5 | 10.30 | 0.310 | 12.70 | 0.090 | 0.220 | 0.984 | 37.3 |
| 6 | 5.00 | 0.360 | 13.00 | 0.040 | 0.230 | 0.985 | 38.4 |
| 7 | 5.70 | 0.410 | 13.30 | 0.130 | 0.240 | 0.986 | 39.5 |
| 8 | 6.40 | 0.460 | 13.60 | 0.080 | 0.250 | 0.987 | 18.6 |
| 9 | 7.10 | 0.510 | 13.90 | 0.170 | 0.260 | 0.988 | 19.7 |
| 10 | 7.80 | 0.560 | 14.20 | 0.120 | 0.270 | 0.989 | 20.8 |
| 11 | 8.50 | 0.610 | 14.50 | 0.070 | 0.280 | 0.990 | 21.9 |
| 12 | 9.20 | 0.660 | 14.80 | 0.160 | 0.290 | 0.991 | 23.0 |
| 13 | 9.90 | 0.710 | 15.10 | 0.110 | 0.300 | 0.992 | 24.1 |
| 14 | 10.60 | 0.760 | 15.40 | 0.060 | 0.310 | 0.993 | 25.2 |
| 15 | 5.30 | 0.810 | 15.70 | 0.150 | 0.320 | 0.994 | 26.3 |
| 16 | 6.00 | 0.860 | 16.00 | 0.100 | 0.330 | 0.995 | 27.4 |
| 17 | 6.70 | 0.910 | 16.30 | 0.050 | 0.340 | 0.996 | 28.5 |
| 18 | 7.40 | 0.960 | 16.60 | 0.140 | 0.350 | 0.997 | 29.6 |

The eighteen replicates of SC-2206 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2207

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 8.80 | 1.120 | 13.20 | 0.060 | 0.250 | 0.983 | 35.2 |
| 2 | 9.50 | 1.170 | 13.50 | 0.150 | 0.260 | 0.984 | 36.3 |
| 3 | 10.20 | 0.320 | 13.80 | 0.100 | 0.270 | 0.985 | 37.4 |
| 4 | 10.90 | 0.370 | 14.10 | 0.050 | 0.280 | 0.986 | 38.5 |
| 5 | 5.60 | 0.420 | 14.40 | 0.140 | 0.290 | 0.987 | 39.6 |
| 6 | 6.30 | 0.470 | 14.70 | 0.090 | 0.300 | 0.988 | 18.7 |
| 7 | 7.00 | 0.520 | 15.00 | 0.040 | 0.310 | 0.989 | 19.8 |
| 8 | 7.70 | 0.570 | 15.30 | 0.130 | 0.320 | 0.990 | 20.9 |
| 9 | 8.40 | 0.620 | 15.60 | 0.080 | 0.330 | 0.991 | 22.0 |
| 10 | 9.10 | 0.670 | 15.90 | 0.170 | 0.340 | 0.992 | 23.1 |
| 11 | 9.80 | 0.720 | 16.20 | 0.120 | 0.350 | 0.993 | 24.2 |
| 12 | 10.50 | 0.770 | 16.50 | 0.070 | 0.360 | 0.994 | 25.3 |
| 13 | 5.20 | 0.820 | 16.80 | 0.160 | 0.370 | 0.995 | 26.4 |
| 14 | 5.90 | 0.870 | 9.10 | 0.110 | 0.380 | 0.996 | 27.5 |
| 15 | 6.60 | 0.920 | 9.40 | 0.060 | 0.390 | 0.997 | 28.6 |
| 16 | 7.30 | 0.970 | 9.70 | 0.150 | 0.400 | 0.998 | 29.7 |
| 17 | 8.00 | 1.020 | 10.00 | 0.100 | 0.410 | 0.980 | 30.8 |
| 18 | 8.70 | 1.070 | 10.30 | 0.050 | 0.420 | 0.981 | 31.9 |

The eighteen replicates of SC-2207 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2208

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 10.10 | 0.330 | 14.90 | 0.110 | 0.320 | 0.986 | 37.5 |
| 2 | 10.80 | 0.380 | 15.20 | 0.060 | 0.330 | 0.987 | 38.6 |
| 3 | 5.50 | 0.430 | 15.50 | 0.150 | 0.340 | 0.988 | 39.7 |
| 4 | 6.20 | 0.480 | 15.80 | 0.100 | 0.350 | 0.989 | 18.8 |
| 5 | 6.90 | 0.530 | 16.10 | 0.050 | 0.360 | 0.990 | 19.9 |
| 6 | 7.60 | 0.580 | 16.40 | 0.140 | 0.370 | 0.991 | 21.0 |
| 7 | 8.30 | 0.630 | 16.70 | 0.090 | 0.380 | 0.992 | 22.1 |
| 8 | 9.00 | 0.680 | 9.00 | 0.040 | 0.390 | 0.993 | 23.2 |
| 9 | 9.70 | 0.730 | 9.30 | 0.130 | 0.400 | 0.994 | 24.3 |
| 10 | 10.40 | 0.780 | 9.60 | 0.080 | 0.410 | 0.995 | 25.4 |
| 11 | 5.10 | 0.830 | 9.90 | 0.170 | 0.420 | 0.996 | 26.5 |
| 12 | 5.80 | 0.880 | 10.20 | 0.120 | 0.430 | 0.997 | 27.6 |
| 13 | 6.50 | 0.930 | 10.50 | 0.070 | 0.440 | 0.998 | 28.7 |
| 14 | 7.20 | 0.980 | 10.80 | 0.160 | 0.100 | 0.980 | 29.8 |
| 15 | 7.90 | 1.030 | 11.10 | 0.110 | 0.110 | 0.981 | 30.9 |
| 16 | 8.60 | 1.080 | 11.40 | 0.060 | 0.120 | 0.982 | 32.0 |
| 17 | 9.30 | 1.130 | 11.70 | 0.150 | 0.130 | 0.983 | 33.1 |
| 18 | 10.00 | 1.180 | 12.00 | 0.100 | 0.140 | 0.984 | 34.2 |

The eighteen replicates of SC-2208 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2209

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 5.40 | 0.440 | 16.60 | 0.160 | 0.390 | 0.989 | 39.8 |
| 2 | 6.10 | 0.490 | 16.90 | 0.110 | 0.400 | 0.990 | 18.9 |
| 3 | 6.80 | 0.540 | 9.20 | 0.060 | 0.410 | 0.991 | 20.0 |
| 4 | 7.50 | 0.590 | 9.50 | 0.150 | 0.420 | 0.992 | 21.1 |
| 5 | 8.20 | 0.640 | 9.80 | 0.100 | 0.430 | 0.993 | 22.2 |
| 6 | 8.90 | 0.690 | 10.10 | 0.050 | 0.440 | 0.994 | 23.3 |
| 7 | 9.60 | 0.740 | 10.40 | 0.140 | 0.100 | 0.995 | 24.4 |
| 8 | 10.30 | 0.790 | 10.70 | 0.090 | 0.110 | 0.996 | 25.5 |
| 9 | 5.00 | 0.840 | 11.00 | 0.040 | 0.120 | 0.997 | 26.6 |
| 10 | 5.70 | 0.890 | 11.30 | 0.130 | 0.130 | 0.998 | 27.7 |
| 11 | 6.40 | 0.940 | 11.60 | 0.080 | 0.140 | 0.980 | 28.8 |
| 12 | 7.10 | 0.990 | 11.90 | 0.170 | 0.150 | 0.981 | 29.9 |
| 13 | 7.80 | 1.040 | 12.20 | 0.120 | 0.160 | 0.982 | 31.0 |
| 14 | 8.50 | 1.090 | 12.50 | 0.070 | 0.170 | 0.983 | 32.1 |
| 15 | 9.20 | 1.140 | 12.80 | 0.160 | 0.180 | 0.984 | 33.2 |
| 16 | 9.90 | 1.190 | 13.10 | 0.110 | 0.190 | 0.985 | 34.3 |
| 17 | 10.60 | 0.340 | 13.40 | 0.060 | 0.200 | 0.986 | 35.4 |
| 18 | 5.30 | 0.390 | 13.70 | 0.150 | 0.210 | 0.987 | 36.5 |

The eighteen replicates of SC-2209 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2210

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 6.70 | 0.550 | 10.30 | 0.070 | 0.110 | 0.992 | 20.1 |
| 2 | 7.40 | 0.600 | 10.60 | 0.160 | 0.120 | 0.993 | 21.2 |
| 3 | 8.10 | 0.650 | 10.90 | 0.110 | 0.130 | 0.994 | 22.3 |
| 4 | 8.80 | 0.700 | 11.20 | 0.060 | 0.140 | 0.995 | 23.4 |
| 5 | 9.50 | 0.750 | 11.50 | 0.150 | 0.150 | 0.996 | 24.5 |
| 6 | 10.20 | 0.800 | 11.80 | 0.100 | 0.160 | 0.997 | 25.6 |
| 7 | 10.90 | 0.850 | 12.10 | 0.050 | 0.170 | 0.998 | 26.7 |
| 8 | 5.60 | 0.900 | 12.40 | 0.140 | 0.180 | 0.980 | 27.8 |
| 9 | 6.30 | 0.950 | 12.70 | 0.090 | 0.190 | 0.981 | 28.9 |
| 10 | 7.00 | 1.000 | 13.00 | 0.040 | 0.200 | 0.982 | 30.0 |
| 11 | 7.70 | 1.050 | 13.30 | 0.130 | 0.210 | 0.983 | 31.1 |
| 12 | 8.40 | 1.100 | 13.60 | 0.080 | 0.220 | 0.984 | 32.2 |
| 13 | 9.10 | 1.150 | 13.90 | 0.170 | 0.230 | 0.985 | 33.3 |
| 14 | 9.80 | 0.300 | 14.20 | 0.120 | 0.240 | 0.986 | 34.4 |
| 15 | 10.50 | 0.350 | 14.50 | 0.070 | 0.250 | 0.987 | 35.5 |
| 16 | 5.20 | 0.400 | 14.80 | 0.160 | 0.260 | 0.988 | 36.6 |
| 17 | 5.90 | 0.450 | 15.10 | 0.110 | 0.270 | 0.989 | 37.7 |
| 18 | 6.60 | 0.500 | 15.40 | 0.060 | 0.280 | 0.990 | 38.8 |

The eighteen replicates of SC-2210 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2211

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 8.00 | 0.660 | 12.00 | 0.120 | 0.180 | 0.995 | 22.4 |
| 2 | 8.70 | 0.710 | 12.30 | 0.070 | 0.190 | 0.996 | 23.5 |
| 3 | 9.40 | 0.760 | 12.60 | 0.160 | 0.200 | 0.997 | 24.6 |
| 4 | 10.10 | 0.810 | 12.90 | 0.110 | 0.210 | 0.998 | 25.7 |
| 5 | 10.80 | 0.860 | 13.20 | 0.060 | 0.220 | 0.980 | 26.8 |
| 6 | 5.50 | 0.910 | 13.50 | 0.150 | 0.230 | 0.981 | 27.9 |
| 7 | 6.20 | 0.960 | 13.80 | 0.100 | 0.240 | 0.982 | 29.0 |
| 8 | 6.90 | 1.010 | 14.10 | 0.050 | 0.250 | 0.983 | 30.1 |
| 9 | 7.60 | 1.060 | 14.40 | 0.140 | 0.260 | 0.984 | 31.2 |
| 10 | 8.30 | 1.110 | 14.70 | 0.090 | 0.270 | 0.985 | 32.3 |
| 11 | 9.00 | 1.160 | 15.00 | 0.040 | 0.280 | 0.986 | 33.4 |
| 12 | 9.70 | 0.310 | 15.30 | 0.130 | 0.290 | 0.987 | 34.5 |
| 13 | 10.40 | 0.360 | 15.60 | 0.080 | 0.300 | 0.988 | 35.6 |
| 14 | 5.10 | 0.410 | 15.90 | 0.170 | 0.310 | 0.989 | 36.7 |
| 15 | 5.80 | 0.460 | 16.20 | 0.120 | 0.320 | 0.990 | 37.8 |
| 16 | 6.50 | 0.510 | 16.50 | 0.070 | 0.330 | 0.991 | 38.9 |
| 17 | 7.20 | 0.560 | 16.80 | 0.160 | 0.340 | 0.992 | 18.0 |
| 18 | 7.90 | 0.610 | 9.10 | 0.110 | 0.350 | 0.993 | 19.1 |

The eighteen replicates of SC-2211 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

### Catalogue — SC-2212

| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |
|-----------|---------|-----------|------------|---------|-----------|----|--------|
| 1 | 9.30 | 0.770 | 13.70 | 0.170 | 0.250 | 0.998 | 24.7 |
| 2 | 10.00 | 0.820 | 14.00 | 0.120 | 0.260 | 0.980 | 25.8 |
| 3 | 10.70 | 0.870 | 14.30 | 0.070 | 0.270 | 0.981 | 26.9 |
| 4 | 5.40 | 0.920 | 14.60 | 0.160 | 0.280 | 0.982 | 28.0 |
| 5 | 6.10 | 0.970 | 14.90 | 0.110 | 0.290 | 0.983 | 29.1 |
| 6 | 6.80 | 1.020 | 15.20 | 0.060 | 0.300 | 0.984 | 30.2 |
| 7 | 7.50 | 1.070 | 15.50 | 0.150 | 0.310 | 0.985 | 31.3 |
| 8 | 8.20 | 1.120 | 15.80 | 0.100 | 0.320 | 0.986 | 32.4 |
| 9 | 8.90 | 1.170 | 16.10 | 0.050 | 0.330 | 0.987 | 33.5 |
| 10 | 9.60 | 0.320 | 16.40 | 0.140 | 0.340 | 0.988 | 34.6 |
| 11 | 10.30 | 0.370 | 16.70 | 0.090 | 0.350 | 0.989 | 35.7 |
| 12 | 5.00 | 0.420 | 9.00 | 0.040 | 0.360 | 0.990 | 36.8 |
| 13 | 5.70 | 0.470 | 9.30 | 0.130 | 0.370 | 0.991 | 37.9 |
| 14 | 6.40 | 0.520 | 9.60 | 0.080 | 0.380 | 0.992 | 39.0 |
| 15 | 7.10 | 0.570 | 9.90 | 0.170 | 0.390 | 0.993 | 18.1 |
| 16 | 7.80 | 0.620 | 10.20 | 0.120 | 0.400 | 0.994 | 19.2 |
| 17 | 8.50 | 0.670 | 10.50 | 0.070 | 0.410 | 0.995 | 20.3 |
| 18 | 9.20 | 0.720 | 10.80 | 0.160 | 0.420 | 0.996 | 21.4 |

The eighteen replicates of SC-2212 agree to within the §13 control limits. The replicate spread in the initial settling velocity is the principal contributor to the reported confidence interval, consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility only; the configuration that produced them is the governing §9 configuration in every case.

## §26 Round-Robin Detailed Results (non-binding)

The 2024 inter-laboratory study (§19) is documented in full here. Each participating laboratory analysed the common record for every registry experiment using its then-current configuration. The tables below report each laboratory's recovered initial settling velocity; the spread across laboratories reflects their differing configurations and motivated the standardisation of Revision C.

### Laboratory 1: Meridian (lead)

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 7.00 | 0.460 | 11.00 | 0.040 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2202 | 8.30 | 0.570 | 12.70 | 0.090 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2203 | 9.60 | 0.680 | 14.40 | 0.140 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2204 | 10.90 | 0.790 | 16.10 | 0.050 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2205 | 6.20 | 0.900 | 9.80 | 0.100 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2206 | 7.50 | 1.010 | 11.50 | 0.150 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2207 | 8.80 | 1.120 | 13.20 | 0.060 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2208 | 10.10 | 0.330 | 14.90 | 0.110 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2209 | 5.40 | 0.440 | 16.60 | 0.160 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2210 | 6.70 | 0.550 | 10.30 | 0.070 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2211 | 8.00 | 0.660 | 12.00 | 0.120 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2212 | 9.30 | 0.770 | 13.70 | 0.170 | two-phase, 3/side, cap 5000, z=2.0 |

Meridian (lead) used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

### Laboratory 2: Northvale Geotechnical

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 7.70 | 0.510 | 11.30 | 0.130 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2202 | 9.00 | 0.620 | 13.00 | 0.040 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2203 | 10.30 | 0.730 | 14.70 | 0.090 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2204 | 5.60 | 0.840 | 16.40 | 0.140 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2205 | 6.90 | 0.950 | 10.10 | 0.050 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2206 | 8.20 | 1.060 | 11.80 | 0.100 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2207 | 9.50 | 1.170 | 13.50 | 0.150 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2208 | 10.80 | 0.380 | 15.20 | 0.060 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2209 | 6.10 | 0.490 | 16.90 | 0.110 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2210 | 7.40 | 0.600 | 10.60 | 0.160 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2211 | 8.70 | 0.710 | 12.30 | 0.070 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2212 | 10.00 | 0.820 | 14.00 | 0.120 | two-phase, 3/side, cap 5000, z=2.0 |

Northvale Geotechnical used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

### Laboratory 3: Coastal Sediments Inc.

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 8.40 | 0.560 | 11.60 | 0.080 | single-exp, z=2.0 |
| SC-2202 | 9.70 | 0.670 | 13.30 | 0.130 | single-exp, z=2.0 |
| SC-2203 | 5.00 | 0.780 | 15.00 | 0.040 | single-exp, z=2.0 |
| SC-2204 | 6.30 | 0.890 | 16.70 | 0.090 | single-exp, z=2.0 |
| SC-2205 | 7.60 | 1.000 | 10.40 | 0.140 | single-exp, z=2.0 |
| SC-2206 | 8.90 | 1.110 | 12.10 | 0.050 | single-exp, z=2.0 |
| SC-2207 | 10.20 | 0.320 | 13.80 | 0.100 | single-exp, z=2.0 |
| SC-2208 | 5.50 | 0.430 | 15.50 | 0.150 | single-exp, z=2.0 |
| SC-2209 | 6.80 | 0.540 | 9.20 | 0.060 | single-exp, z=2.0 |
| SC-2210 | 8.10 | 0.650 | 10.90 | 0.110 | single-exp, z=2.0 |
| SC-2211 | 9.40 | 0.760 | 12.60 | 0.160 | single-exp, z=2.0 |
| SC-2212 | 10.70 | 0.870 | 14.30 | 0.070 | single-exp, z=2.0 |

Coastal Sediments Inc. used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

### Laboratory 4: Université du Littoral

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 9.10 | 0.610 | 11.90 | 0.170 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2202 | 10.40 | 0.720 | 13.60 | 0.080 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2203 | 5.70 | 0.830 | 15.30 | 0.130 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2204 | 7.00 | 0.940 | 9.00 | 0.040 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2205 | 8.30 | 1.050 | 10.70 | 0.090 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2206 | 9.60 | 1.160 | 12.40 | 0.140 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2207 | 10.90 | 0.370 | 14.10 | 0.050 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2208 | 6.20 | 0.480 | 15.80 | 0.100 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2209 | 7.50 | 0.590 | 9.50 | 0.150 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2210 | 8.80 | 0.700 | 11.20 | 0.060 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2211 | 10.10 | 0.810 | 12.90 | 0.110 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2212 | 5.40 | 0.920 | 14.60 | 0.160 | two-phase, 3/side, cap 5000, z=2.0 |

Université du Littoral used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

### Laboratory 5: Hokuriku Soil Mechanics

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 9.80 | 0.660 | 12.20 | 0.120 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2202 | 5.10 | 0.770 | 13.90 | 0.170 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2203 | 6.40 | 0.880 | 15.60 | 0.080 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2204 | 7.70 | 0.990 | 9.30 | 0.130 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2205 | 9.00 | 1.100 | 11.00 | 0.040 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2206 | 10.30 | 0.310 | 12.70 | 0.090 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2207 | 5.60 | 0.420 | 14.40 | 0.140 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2208 | 6.90 | 0.530 | 16.10 | 0.050 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2209 | 8.20 | 0.640 | 9.80 | 0.100 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2210 | 9.50 | 0.750 | 11.50 | 0.150 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2211 | 10.80 | 0.860 | 13.20 | 0.060 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2212 | 6.10 | 0.970 | 14.90 | 0.110 | two-phase, 5/side, cap 10000, z=1.96 |

Hokuriku Soil Mechanics used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

### Laboratory 6: Cape Survey Labs

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 10.50 | 0.710 | 12.50 | 0.070 | power-law, z=2.576 |
| SC-2202 | 5.80 | 0.820 | 14.20 | 0.120 | power-law, z=2.576 |
| SC-2203 | 7.10 | 0.930 | 15.90 | 0.170 | power-law, z=2.576 |
| SC-2204 | 8.40 | 1.040 | 9.60 | 0.080 | power-law, z=2.576 |
| SC-2205 | 9.70 | 1.150 | 11.30 | 0.130 | power-law, z=2.576 |
| SC-2206 | 5.00 | 0.360 | 13.00 | 0.040 | power-law, z=2.576 |
| SC-2207 | 6.30 | 0.470 | 14.70 | 0.090 | power-law, z=2.576 |
| SC-2208 | 7.60 | 0.580 | 16.40 | 0.140 | power-law, z=2.576 |
| SC-2209 | 8.90 | 0.690 | 10.10 | 0.050 | power-law, z=2.576 |
| SC-2210 | 10.20 | 0.800 | 11.80 | 0.100 | power-law, z=2.576 |
| SC-2211 | 5.50 | 0.910 | 13.50 | 0.150 | power-law, z=2.576 |
| SC-2212 | 6.80 | 1.020 | 15.20 | 0.060 | power-law, z=2.576 |

Cape Survey Labs used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

### Laboratory 7: Andes Hydrology Group

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 5.20 | 0.760 | 12.80 | 0.160 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2202 | 6.50 | 0.870 | 14.50 | 0.070 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2203 | 7.80 | 0.980 | 16.20 | 0.120 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2204 | 9.10 | 1.090 | 9.90 | 0.170 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2205 | 10.40 | 0.300 | 11.60 | 0.080 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2206 | 5.70 | 0.410 | 13.30 | 0.130 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2207 | 7.00 | 0.520 | 15.00 | 0.040 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2208 | 8.30 | 0.630 | 16.70 | 0.090 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2209 | 9.60 | 0.740 | 10.40 | 0.140 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2210 | 10.90 | 0.850 | 12.10 | 0.050 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2211 | 6.20 | 0.960 | 13.80 | 0.100 | two-phase, 3/side, cap 5000, z=2.0 |
| SC-2212 | 7.50 | 1.070 | 15.50 | 0.150 | two-phase, 3/side, cap 5000, z=2.0 |

Andes Hydrology Group used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

### Laboratory 8: Baltic Particle Science

| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |
|------------|---------|-----------|------------|---------|-------|
| SC-2201 | 5.90 | 0.810 | 13.10 | 0.110 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2202 | 7.20 | 0.920 | 14.80 | 0.160 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2203 | 8.50 | 1.030 | 16.50 | 0.070 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2204 | 9.80 | 1.140 | 10.20 | 0.120 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2205 | 5.10 | 0.350 | 11.90 | 0.170 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2206 | 6.40 | 0.460 | 13.60 | 0.080 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2207 | 7.70 | 0.570 | 15.30 | 0.130 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2208 | 9.00 | 0.680 | 9.00 | 0.040 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2209 | 10.30 | 0.790 | 10.70 | 0.090 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2210 | 5.60 | 0.900 | 12.40 | 0.140 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2211 | 6.90 | 1.010 | 14.10 | 0.050 | two-phase, 5/side, cap 10000, z=1.96 |
| SC-2212 | 8.20 | 1.120 | 15.80 | 0.100 | two-phase, 5/side, cap 10000, z=1.96 |

Baltic Particle Science used the configuration noted above throughout the round. Only the rows where a laboratory used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage factor correspond to the Revision C governing configuration; the remaining configurations are recorded for traceability and are superseded.

## §27 Frequently Asked Questions (non-binding)

**Q: Which model should I use for experiment 7?**

The two-phase model of §9.1. The single-exponential model is a superseded Revision A model and the power-law model was never adopted; neither is used under Revision C.

**Q: How many points must lie on each side of the breakpoint?**

At least five (§9.2). Revision B required only three; that requirement is superseded. The §10 worked example and the round-robin rows that used three points per side are not governing.

**Q: What initial guesses should the optimiser use?**

v1 = 1.0 cm/s and k = 0.05 1/s, with h_inf started at the minimum observed height (§9.3). The historical guesses of 0.5 cm/s and 0.10 1/s (Appendix B, Revisions A/B) are superseded.

**Q: What is the optimiser evaluation cap?**

10000 (§9.3). The older cap of 5000 is superseded.

**Q: Which coverage factor applies to the confidence intervals?**

1.96 (§9.4). The factor 2.0 used in Revisions A/B is superseded, and 2.576 is a 99% factor used only on explicit client request.

**Q: Which value of gravity do I use?**

9.81 m/s² (§8). The more precise standard-gravity value 9.80665 m/s² (Appendix A) is not used in this reduction.

**Q: How do I convert the timing channel?**

Divide milliseconds by 1000 to obtain seconds (§8). The minute conversion (60000 ms) in Appendix A is for reading old logbooks only.

**Q: In what unit is the effective diameter reported?**

Micrometres (§8 and §9.5).

**Q: The database calibration differs from the §17 table — which do I use?**

The database record for the experiment's assigned sensor (§5). The §17 table is representative context, and the withdrawn laboratory-wide constant is never used.

## §28 Reference Interface-Height Digests (non-binding)

For each registry experiment, a digest of the mean interface height across the validation replicates is tabulated below at fixed elapsed times. The digests document the qualitative settling behaviour — an approximately linear free-settling descent followed by an exponential approach to the final bed height — and are provided for context and for cross-checking an analysis pipeline. They are not configuration values and they are not the data analysed by the practice (which is served per experiment through the acquisition channels, in milliseconds and raw levels).

### Digest — SC-2201

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 40.00 | 0.04 | free-settling |
| 2.0 | 39.08 | 0.05 | free-settling |
| 4.0 | 38.16 | 0.06 | free-settling |
| 6.0 | 37.24 | 0.07 | free-settling |
| 8.0 | 35.77 | 0.08 | compression |
| 10.0 | 33.86 | 0.09 | compression |
| 12.0 | 32.11 | 0.03 | compression |
| 14.0 | 30.48 | 0.04 | compression |
| 16.0 | 28.99 | 0.05 | compression |
| 18.0 | 27.60 | 0.06 | compression |
| 20.0 | 26.33 | 0.07 | compression |
| 22.0 | 25.15 | 0.08 | compression |
| 24.0 | 24.06 | 0.09 | compression |
| 26.0 | 23.06 | 0.03 | compression |
| 28.0 | 22.13 | 0.04 | compression |
| 30.0 | 21.27 | 0.05 | compression |
| 32.0 | 20.48 | 0.06 | compression |
| 34.0 | 19.75 | 0.07 | compression |
| 36.0 | 19.08 | 0.08 | compression |
| 38.0 | 18.46 | 0.09 | compression |
| 40.0 | 17.89 | 0.03 | compression |
| 42.0 | 17.36 | 0.04 | compression |
| 44.0 | 16.87 | 0.05 | compression |
| 46.0 | 16.42 | 0.06 | compression |
| 48.0 | 16.00 | 0.07 | compression |
| 50.0 | 15.62 | 0.08 | compression |
| 52.0 | 15.26 | 0.09 | compression |
| 54.0 | 14.93 | 0.03 | compression |
| 56.0 | 14.63 | 0.04 | compression |
| 58.0 | 14.35 | 0.05 | compression |
| 60.0 | 14.09 | 0.06 | compression |
| 62.0 | 13.86 | 0.07 | compression |
| 64.0 | 13.64 | 0.08 | compression |
| 66.0 | 13.43 | 0.09 | compression |
| 68.0 | 13.25 | 0.03 | compression |
| 70.0 | 13.07 | 0.04 | compression |
| 72.0 | 12.91 | 0.05 | compression |
| 74.0 | 12.77 | 0.06 | compression |
| 76.0 | 12.63 | 0.07 | compression |
| 78.0 | 12.51 | 0.08 | compression |
| 80.0 | 12.39 | 0.09 | compression |
| 82.0 | 12.28 | 0.03 | compression |
| 84.0 | 12.18 | 0.04 | compression |
| 86.0 | 12.09 | 0.05 | compression |
| 88.0 | 12.01 | 0.06 | compression |
| 90.0 | 11.93 | 0.07 | compression |
| 92.0 | 11.86 | 0.08 | compression |
| 94.0 | 11.79 | 0.09 | compression |
| 96.0 | 11.73 | 0.03 | compression |
| 98.0 | 11.68 | 0.04 | compression |
| 100.0 | 11.62 | 0.05 | compression |
| 102.0 | 11.58 | 0.06 | compression |
| 104.0 | 11.53 | 0.07 | compression |
| 106.0 | 11.49 | 0.08 | compression |
| 108.0 | 11.45 | 0.09 | compression |
| 110.0 | 11.42 | 0.03 | compression |
| 112.0 | 11.39 | 0.04 | compression |
| 114.0 | 11.36 | 0.05 | compression |
| 116.0 | 11.33 | 0.06 | compression |
| 118.0 | 11.30 | 0.07 | compression |
| 120.0 | 11.28 | 0.08 | compression |
| 122.0 | 11.26 | 0.09 | compression |
| 124.0 | 11.24 | 0.03 | compression |
| 126.0 | 11.22 | 0.04 | compression |
| 128.0 | 11.20 | 0.05 | compression |
| 130.0 | 11.19 | 0.06 | compression |
| 132.0 | 11.17 | 0.07 | compression |
| 134.0 | 11.16 | 0.08 | compression |
| 136.0 | 11.15 | 0.09 | compression |
| 138.0 | 11.14 | 0.03 | compression |
| 140.0 | 11.13 | 0.04 | compression |
| 142.0 | 11.12 | 0.05 | compression |

The SC-2201 digest shows the breakpoint near 7.0 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2202

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 38.50 | 0.05 | free-settling |
| 2.0 | 37.36 | 0.06 | free-settling |
| 4.0 | 36.22 | 0.07 | free-settling |
| 6.0 | 35.08 | 0.08 | free-settling |
| 8.0 | 33.94 | 0.09 | free-settling |
| 10.0 | 30.78 | 0.03 | compression |
| 12.0 | 27.80 | 0.04 | compression |
| 14.0 | 25.31 | 0.05 | compression |
| 16.0 | 23.24 | 0.06 | compression |
| 18.0 | 21.50 | 0.07 | compression |
| 20.0 | 20.05 | 0.08 | compression |
| 22.0 | 18.84 | 0.09 | compression |
| 24.0 | 17.83 | 0.03 | compression |
| 26.0 | 16.98 | 0.04 | compression |
| 28.0 | 16.28 | 0.05 | compression |
| 30.0 | 15.69 | 0.06 | compression |
| 32.0 | 15.20 | 0.07 | compression |
| 34.0 | 14.79 | 0.08 | compression |
| 36.0 | 14.44 | 0.09 | compression |
| 38.0 | 14.15 | 0.03 | compression |
| 40.0 | 13.92 | 0.04 | compression |
| 42.0 | 13.71 | 0.05 | compression |
| 44.0 | 13.55 | 0.06 | compression |
| 46.0 | 13.41 | 0.07 | compression |
| 48.0 | 13.29 | 0.08 | compression |
| 50.0 | 13.19 | 0.09 | compression |
| 52.0 | 13.11 | 0.03 | compression |
| 54.0 | 13.04 | 0.04 | compression |
| 56.0 | 12.99 | 0.05 | compression |
| 58.0 | 12.94 | 0.06 | compression |
| 60.0 | 12.90 | 0.07 | compression |
| 62.0 | 12.87 | 0.08 | compression |
| 64.0 | 12.84 | 0.09 | compression |
| 66.0 | 12.82 | 0.03 | compression |
| 68.0 | 12.80 | 0.04 | compression |
| 70.0 | 12.78 | 0.05 | compression |
| 72.0 | 12.77 | 0.06 | compression |
| 74.0 | 12.76 | 0.07 | compression |
| 76.0 | 12.75 | 0.08 | compression |
| 78.0 | 12.74 | 0.09 | compression |
| 80.0 | 12.73 | 0.03 | compression |
| 82.0 | 12.73 | 0.04 | compression |
| 84.0 | 12.72 | 0.05 | compression |
| 86.0 | 12.72 | 0.06 | compression |
| 88.0 | 12.72 | 0.07 | compression |
| 90.0 | 12.71 | 0.08 | compression |
| 92.0 | 12.71 | 0.09 | compression |
| 94.0 | 12.71 | 0.03 | compression |
| 96.0 | 12.71 | 0.04 | compression |
| 98.0 | 12.71 | 0.05 | compression |
| 100.0 | 12.71 | 0.06 | compression |
| 102.0 | 12.70 | 0.07 | compression |
| 104.0 | 12.70 | 0.08 | compression |
| 106.0 | 12.70 | 0.09 | compression |
| 108.0 | 12.70 | 0.03 | compression |
| 110.0 | 12.70 | 0.04 | compression |
| 112.0 | 12.70 | 0.05 | compression |
| 114.0 | 12.70 | 0.06 | compression |
| 116.0 | 12.70 | 0.07 | compression |
| 118.0 | 12.70 | 0.08 | compression |
| 120.0 | 12.70 | 0.09 | compression |
| 122.0 | 12.70 | 0.03 | compression |
| 124.0 | 12.70 | 0.04 | compression |
| 126.0 | 12.70 | 0.05 | compression |
| 128.0 | 12.70 | 0.06 | compression |
| 130.0 | 12.70 | 0.07 | compression |
| 132.0 | 12.70 | 0.08 | compression |
| 134.0 | 12.70 | 0.09 | compression |
| 136.0 | 12.70 | 0.03 | compression |
| 138.0 | 12.70 | 0.04 | compression |
| 140.0 | 12.70 | 0.05 | compression |
| 142.0 | 12.70 | 0.06 | compression |

The SC-2202 digest shows the breakpoint near 8.3 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2203

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 45.00 | 0.06 | free-settling |
| 2.0 | 43.64 | 0.07 | free-settling |
| 4.0 | 42.28 | 0.08 | free-settling |
| 6.0 | 40.92 | 0.09 | free-settling |
| 8.0 | 39.56 | 0.03 | free-settling |
| 10.0 | 37.16 | 0.04 | compression |
| 12.0 | 31.60 | 0.05 | compression |
| 14.0 | 27.40 | 0.06 | compression |
| 16.0 | 24.23 | 0.07 | compression |
| 18.0 | 21.83 | 0.08 | compression |
| 20.0 | 20.01 | 0.09 | compression |
| 22.0 | 18.64 | 0.03 | compression |
| 24.0 | 17.61 | 0.04 | compression |
| 26.0 | 16.82 | 0.05 | compression |
| 28.0 | 16.23 | 0.06 | compression |
| 30.0 | 15.78 | 0.07 | compression |
| 32.0 | 15.45 | 0.08 | compression |
| 34.0 | 15.19 | 0.09 | compression |
| 36.0 | 15.00 | 0.03 | compression |
| 38.0 | 14.85 | 0.04 | compression |
| 40.0 | 14.74 | 0.05 | compression |
| 42.0 | 14.66 | 0.06 | compression |
| 44.0 | 14.59 | 0.07 | compression |
| 46.0 | 14.55 | 0.08 | compression |
| 48.0 | 14.51 | 0.09 | compression |
| 50.0 | 14.48 | 0.03 | compression |
| 52.0 | 14.46 | 0.04 | compression |
| 54.0 | 14.45 | 0.05 | compression |
| 56.0 | 14.44 | 0.06 | compression |
| 58.0 | 14.43 | 0.07 | compression |
| 60.0 | 14.42 | 0.08 | compression |
| 62.0 | 14.42 | 0.09 | compression |
| 64.0 | 14.41 | 0.03 | compression |
| 66.0 | 14.41 | 0.04 | compression |
| 68.0 | 14.41 | 0.05 | compression |
| 70.0 | 14.41 | 0.06 | compression |
| 72.0 | 14.40 | 0.07 | compression |
| 74.0 | 14.40 | 0.08 | compression |
| 76.0 | 14.40 | 0.09 | compression |
| 78.0 | 14.40 | 0.03 | compression |
| 80.0 | 14.40 | 0.04 | compression |
| 82.0 | 14.40 | 0.05 | compression |
| 84.0 | 14.40 | 0.06 | compression |
| 86.0 | 14.40 | 0.07 | compression |
| 88.0 | 14.40 | 0.08 | compression |
| 90.0 | 14.40 | 0.09 | compression |
| 92.0 | 14.40 | 0.03 | compression |
| 94.0 | 14.40 | 0.04 | compression |
| 96.0 | 14.40 | 0.05 | compression |
| 98.0 | 14.40 | 0.06 | compression |
| 100.0 | 14.40 | 0.07 | compression |
| 102.0 | 14.40 | 0.08 | compression |
| 104.0 | 14.40 | 0.09 | compression |
| 106.0 | 14.40 | 0.03 | compression |
| 108.0 | 14.40 | 0.04 | compression |
| 110.0 | 14.40 | 0.05 | compression |
| 112.0 | 14.40 | 0.06 | compression |
| 114.0 | 14.40 | 0.07 | compression |
| 116.0 | 14.40 | 0.08 | compression |
| 118.0 | 14.40 | 0.09 | compression |
| 120.0 | 14.40 | 0.03 | compression |
| 122.0 | 14.40 | 0.04 | compression |
| 124.0 | 14.40 | 0.05 | compression |
| 126.0 | 14.40 | 0.06 | compression |
| 128.0 | 14.40 | 0.07 | compression |
| 130.0 | 14.40 | 0.08 | compression |
| 132.0 | 14.40 | 0.09 | compression |
| 134.0 | 14.40 | 0.03 | compression |
| 136.0 | 14.40 | 0.04 | compression |
| 138.0 | 14.40 | 0.05 | compression |
| 140.0 | 14.40 | 0.06 | compression |
| 142.0 | 14.40 | 0.07 | compression |

The SC-2203 digest shows the breakpoint near 9.6 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2204

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 42.00 | 0.07 | free-settling |
| 2.0 | 40.42 | 0.08 | free-settling |
| 4.0 | 38.84 | 0.09 | free-settling |
| 6.0 | 37.26 | 0.03 | free-settling |
| 8.0 | 35.68 | 0.04 | free-settling |
| 10.0 | 34.10 | 0.05 | free-settling |
| 12.0 | 32.46 | 0.06 | compression |
| 14.0 | 30.91 | 0.07 | compression |
| 16.0 | 29.50 | 0.08 | compression |
| 18.0 | 28.22 | 0.09 | compression |
| 20.0 | 27.07 | 0.03 | compression |
| 22.0 | 26.03 | 0.04 | compression |
| 24.0 | 25.08 | 0.05 | compression |
| 26.0 | 24.23 | 0.06 | compression |
| 28.0 | 23.45 | 0.07 | compression |
| 30.0 | 22.75 | 0.08 | compression |
| 32.0 | 22.12 | 0.09 | compression |
| 34.0 | 21.55 | 0.03 | compression |
| 36.0 | 21.03 | 0.04 | compression |
| 38.0 | 20.56 | 0.05 | compression |
| 40.0 | 20.14 | 0.06 | compression |
| 42.0 | 19.75 | 0.07 | compression |
| 44.0 | 19.40 | 0.08 | compression |
| 46.0 | 19.09 | 0.09 | compression |
| 48.0 | 18.80 | 0.03 | compression |
| 50.0 | 18.55 | 0.04 | compression |
| 52.0 | 18.31 | 0.05 | compression |
| 54.0 | 18.10 | 0.06 | compression |
| 56.0 | 17.91 | 0.07 | compression |
| 58.0 | 17.74 | 0.08 | compression |
| 60.0 | 17.58 | 0.09 | compression |
| 62.0 | 17.44 | 0.03 | compression |
| 64.0 | 17.32 | 0.04 | compression |
| 66.0 | 17.20 | 0.05 | compression |
| 68.0 | 17.10 | 0.06 | compression |
| 70.0 | 17.00 | 0.07 | compression |
| 72.0 | 16.91 | 0.08 | compression |
| 74.0 | 16.84 | 0.09 | compression |
| 76.0 | 16.77 | 0.03 | compression |
| 78.0 | 16.70 | 0.04 | compression |
| 80.0 | 16.65 | 0.05 | compression |
| 82.0 | 16.59 | 0.06 | compression |
| 84.0 | 16.55 | 0.07 | compression |
| 86.0 | 16.50 | 0.08 | compression |
| 88.0 | 16.47 | 0.09 | compression |
| 90.0 | 16.43 | 0.03 | compression |
| 92.0 | 16.40 | 0.04 | compression |
| 94.0 | 16.37 | 0.05 | compression |
| 96.0 | 16.35 | 0.06 | compression |
| 98.0 | 16.32 | 0.07 | compression |
| 100.0 | 16.30 | 0.08 | compression |
| 102.0 | 16.28 | 0.09 | compression |
| 104.0 | 16.26 | 0.03 | compression |
| 106.0 | 16.25 | 0.04 | compression |
| 108.0 | 16.23 | 0.05 | compression |
| 110.0 | 16.22 | 0.06 | compression |
| 112.0 | 16.21 | 0.07 | compression |
| 114.0 | 16.20 | 0.08 | compression |
| 116.0 | 16.19 | 0.09 | compression |
| 118.0 | 16.18 | 0.03 | compression |
| 120.0 | 16.17 | 0.04 | compression |
| 122.0 | 16.17 | 0.05 | compression |
| 124.0 | 16.16 | 0.06 | compression |
| 126.0 | 16.15 | 0.07 | compression |
| 128.0 | 16.15 | 0.08 | compression |
| 130.0 | 16.14 | 0.09 | compression |
| 132.0 | 16.14 | 0.03 | compression |
| 134.0 | 16.14 | 0.04 | compression |
| 136.0 | 16.13 | 0.05 | compression |
| 138.0 | 16.13 | 0.06 | compression |
| 140.0 | 16.13 | 0.07 | compression |
| 142.0 | 16.12 | 0.08 | compression |

The SC-2204 digest shows the breakpoint near 10.9 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2205

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 41.00 | 0.08 | free-settling |
| 2.0 | 39.20 | 0.09 | free-settling |
| 4.0 | 37.40 | 0.03 | free-settling |
| 6.0 | 35.60 | 0.04 | free-settling |
| 8.0 | 31.20 | 0.05 | compression |
| 10.0 | 27.32 | 0.06 | compression |
| 12.0 | 24.14 | 0.07 | compression |
| 14.0 | 21.54 | 0.08 | compression |
| 16.0 | 19.42 | 0.09 | compression |
| 18.0 | 17.67 | 0.03 | compression |
| 20.0 | 16.25 | 0.04 | compression |
| 22.0 | 15.08 | 0.05 | compression |
| 24.0 | 14.12 | 0.06 | compression |
| 26.0 | 13.34 | 0.07 | compression |
| 28.0 | 12.70 | 0.08 | compression |
| 30.0 | 12.17 | 0.09 | compression |
| 32.0 | 11.74 | 0.03 | compression |
| 34.0 | 11.39 | 0.04 | compression |
| 36.0 | 11.10 | 0.05 | compression |
| 38.0 | 10.87 | 0.06 | compression |
| 40.0 | 10.67 | 0.07 | compression |
| 42.0 | 10.51 | 0.08 | compression |
| 44.0 | 10.38 | 0.09 | compression |
| 46.0 | 10.28 | 0.03 | compression |
| 48.0 | 10.19 | 0.04 | compression |
| 50.0 | 10.12 | 0.05 | compression |
| 52.0 | 10.06 | 0.06 | compression |
| 54.0 | 10.02 | 0.07 | compression |
| 56.0 | 9.98 | 0.08 | compression |
| 58.0 | 9.94 | 0.09 | compression |
| 60.0 | 9.92 | 0.03 | compression |
| 62.0 | 9.90 | 0.04 | compression |
| 64.0 | 9.88 | 0.05 | compression |
| 66.0 | 9.86 | 0.06 | compression |
| 68.0 | 9.85 | 0.07 | compression |
| 70.0 | 9.84 | 0.08 | compression |
| 72.0 | 9.84 | 0.09 | compression |
| 74.0 | 9.83 | 0.03 | compression |
| 76.0 | 9.82 | 0.04 | compression |
| 78.0 | 9.82 | 0.05 | compression |
| 80.0 | 9.82 | 0.06 | compression |
| 82.0 | 9.81 | 0.07 | compression |
| 84.0 | 9.81 | 0.08 | compression |
| 86.0 | 9.81 | 0.09 | compression |
| 88.0 | 9.81 | 0.03 | compression |
| 90.0 | 9.81 | 0.04 | compression |
| 92.0 | 9.80 | 0.05 | compression |
| 94.0 | 9.80 | 0.06 | compression |
| 96.0 | 9.80 | 0.07 | compression |
| 98.0 | 9.80 | 0.08 | compression |
| 100.0 | 9.80 | 0.09 | compression |
| 102.0 | 9.80 | 0.03 | compression |
| 104.0 | 9.80 | 0.04 | compression |
| 106.0 | 9.80 | 0.05 | compression |
| 108.0 | 9.80 | 0.06 | compression |
| 110.0 | 9.80 | 0.07 | compression |
| 112.0 | 9.80 | 0.08 | compression |
| 114.0 | 9.80 | 0.09 | compression |
| 116.0 | 9.80 | 0.03 | compression |
| 118.0 | 9.80 | 0.04 | compression |
| 120.0 | 9.80 | 0.05 | compression |
| 122.0 | 9.80 | 0.06 | compression |
| 124.0 | 9.80 | 0.07 | compression |
| 126.0 | 9.80 | 0.08 | compression |
| 128.0 | 9.80 | 0.09 | compression |
| 130.0 | 9.80 | 0.03 | compression |
| 132.0 | 9.80 | 0.04 | compression |
| 134.0 | 9.80 | 0.05 | compression |
| 136.0 | 9.80 | 0.06 | compression |
| 138.0 | 9.80 | 0.07 | compression |
| 140.0 | 9.80 | 0.08 | compression |
| 142.0 | 9.80 | 0.09 | compression |

The SC-2205 digest shows the breakpoint near 6.2 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2206

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 44.00 | 0.09 | free-settling |
| 2.0 | 41.98 | 0.03 | free-settling |
| 4.0 | 39.96 | 0.04 | free-settling |
| 6.0 | 37.94 | 0.05 | free-settling |
| 8.0 | 34.62 | 0.06 | compression |
| 10.0 | 28.63 | 0.07 | compression |
| 12.0 | 24.19 | 0.08 | compression |
| 14.0 | 20.90 | 0.09 | compression |
| 16.0 | 18.46 | 0.03 | compression |
| 18.0 | 16.66 | 0.04 | compression |
| 20.0 | 15.32 | 0.05 | compression |
| 22.0 | 14.33 | 0.06 | compression |
| 24.0 | 13.60 | 0.07 | compression |
| 26.0 | 13.05 | 0.08 | compression |
| 28.0 | 12.65 | 0.09 | compression |
| 30.0 | 12.35 | 0.03 | compression |
| 32.0 | 12.13 | 0.04 | compression |
| 34.0 | 11.97 | 0.05 | compression |
| 36.0 | 11.85 | 0.06 | compression |
| 38.0 | 11.76 | 0.07 | compression |
| 40.0 | 11.69 | 0.08 | compression |
| 42.0 | 11.64 | 0.09 | compression |
| 44.0 | 11.60 | 0.03 | compression |
| 46.0 | 11.58 | 0.04 | compression |
| 48.0 | 11.56 | 0.05 | compression |
| 50.0 | 11.54 | 0.06 | compression |
| 52.0 | 11.53 | 0.07 | compression |
| 54.0 | 11.52 | 0.08 | compression |
| 56.0 | 11.52 | 0.09 | compression |
| 58.0 | 11.51 | 0.03 | compression |
| 60.0 | 11.51 | 0.04 | compression |
| 62.0 | 11.51 | 0.05 | compression |
| 64.0 | 11.51 | 0.06 | compression |
| 66.0 | 11.50 | 0.07 | compression |
| 68.0 | 11.50 | 0.08 | compression |
| 70.0 | 11.50 | 0.09 | compression |
| 72.0 | 11.50 | 0.03 | compression |
| 74.0 | 11.50 | 0.04 | compression |
| 76.0 | 11.50 | 0.05 | compression |
| 78.0 | 11.50 | 0.06 | compression |
| 80.0 | 11.50 | 0.07 | compression |
| 82.0 | 11.50 | 0.08 | compression |
| 84.0 | 11.50 | 0.09 | compression |
| 86.0 | 11.50 | 0.03 | compression |
| 88.0 | 11.50 | 0.04 | compression |
| 90.0 | 11.50 | 0.05 | compression |
| 92.0 | 11.50 | 0.06 | compression |
| 94.0 | 11.50 | 0.07 | compression |
| 96.0 | 11.50 | 0.08 | compression |
| 98.0 | 11.50 | 0.09 | compression |
| 100.0 | 11.50 | 0.03 | compression |
| 102.0 | 11.50 | 0.04 | compression |
| 104.0 | 11.50 | 0.05 | compression |
| 106.0 | 11.50 | 0.06 | compression |
| 108.0 | 11.50 | 0.07 | compression |
| 110.0 | 11.50 | 0.08 | compression |
| 112.0 | 11.50 | 0.09 | compression |
| 114.0 | 11.50 | 0.03 | compression |
| 116.0 | 11.50 | 0.04 | compression |
| 118.0 | 11.50 | 0.05 | compression |
| 120.0 | 11.50 | 0.06 | compression |
| 122.0 | 11.50 | 0.07 | compression |
| 124.0 | 11.50 | 0.08 | compression |
| 126.0 | 11.50 | 0.09 | compression |
| 128.0 | 11.50 | 0.03 | compression |
| 130.0 | 11.50 | 0.04 | compression |
| 132.0 | 11.50 | 0.05 | compression |
| 134.0 | 11.50 | 0.06 | compression |
| 136.0 | 11.50 | 0.07 | compression |
| 138.0 | 11.50 | 0.08 | compression |
| 140.0 | 11.50 | 0.09 | compression |
| 142.0 | 11.50 | 0.03 | compression |

The SC-2206 digest shows the breakpoint near 7.5 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2207

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 42.00 | 0.03 | free-settling |
| 2.0 | 39.76 | 0.04 | free-settling |
| 4.0 | 37.52 | 0.05 | free-settling |
| 6.0 | 35.28 | 0.06 | free-settling |
| 8.0 | 33.04 | 0.07 | free-settling |
| 10.0 | 30.83 | 0.08 | compression |
| 12.0 | 28.83 | 0.09 | compression |
| 14.0 | 27.07 | 0.03 | compression |
| 16.0 | 25.50 | 0.04 | compression |
| 18.0 | 24.11 | 0.05 | compression |
| 20.0 | 22.87 | 0.06 | compression |
| 22.0 | 21.78 | 0.07 | compression |
| 24.0 | 20.81 | 0.08 | compression |
| 26.0 | 19.95 | 0.09 | compression |
| 28.0 | 19.19 | 0.03 | compression |
| 30.0 | 18.51 | 0.04 | compression |
| 32.0 | 17.91 | 0.05 | compression |
| 34.0 | 17.38 | 0.06 | compression |
| 36.0 | 16.90 | 0.07 | compression |
| 38.0 | 16.49 | 0.08 | compression |
| 40.0 | 16.11 | 0.09 | compression |
| 42.0 | 15.78 | 0.03 | compression |
| 44.0 | 15.49 | 0.04 | compression |
| 46.0 | 15.23 | 0.05 | compression |
| 48.0 | 15.00 | 0.06 | compression |
| 50.0 | 14.80 | 0.07 | compression |
| 52.0 | 14.62 | 0.08 | compression |
| 54.0 | 14.46 | 0.09 | compression |
| 56.0 | 14.32 | 0.03 | compression |
| 58.0 | 14.19 | 0.04 | compression |
| 60.0 | 14.08 | 0.05 | compression |
| 62.0 | 13.98 | 0.06 | compression |
| 64.0 | 13.89 | 0.07 | compression |
| 66.0 | 13.81 | 0.08 | compression |
| 68.0 | 13.74 | 0.09 | compression |
| 70.0 | 13.68 | 0.03 | compression |
| 72.0 | 13.63 | 0.04 | compression |
| 74.0 | 13.58 | 0.05 | compression |
| 76.0 | 13.54 | 0.06 | compression |
| 78.0 | 13.50 | 0.07 | compression |
| 80.0 | 13.46 | 0.08 | compression |
| 82.0 | 13.43 | 0.09 | compression |
| 84.0 | 13.41 | 0.03 | compression |
| 86.0 | 13.38 | 0.04 | compression |
| 88.0 | 13.36 | 0.05 | compression |
| 90.0 | 13.35 | 0.06 | compression |
| 92.0 | 13.33 | 0.07 | compression |
| 94.0 | 13.31 | 0.08 | compression |
| 96.0 | 13.30 | 0.09 | compression |
| 98.0 | 13.29 | 0.03 | compression |
| 100.0 | 13.28 | 0.04 | compression |
| 102.0 | 13.27 | 0.05 | compression |
| 104.0 | 13.26 | 0.06 | compression |
| 106.0 | 13.26 | 0.07 | compression |
| 108.0 | 13.25 | 0.08 | compression |
| 110.0 | 13.24 | 0.09 | compression |
| 112.0 | 13.24 | 0.03 | compression |
| 114.0 | 13.23 | 0.04 | compression |
| 116.0 | 13.23 | 0.05 | compression |
| 118.0 | 13.23 | 0.06 | compression |
| 120.0 | 13.22 | 0.07 | compression |
| 122.0 | 13.22 | 0.08 | compression |
| 124.0 | 13.22 | 0.09 | compression |
| 126.0 | 13.22 | 0.03 | compression |
| 128.0 | 13.21 | 0.04 | compression |
| 130.0 | 13.21 | 0.05 | compression |
| 132.0 | 13.21 | 0.06 | compression |
| 134.0 | 13.21 | 0.07 | compression |
| 136.0 | 13.21 | 0.08 | compression |
| 138.0 | 13.21 | 0.09 | compression |
| 140.0 | 13.21 | 0.03 | compression |
| 142.0 | 13.21 | 0.04 | compression |

The SC-2207 digest shows the breakpoint near 8.8 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2208

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 39.00 | 0.04 | free-settling |
| 2.0 | 38.34 | 0.05 | free-settling |
| 4.0 | 37.68 | 0.06 | free-settling |
| 6.0 | 37.02 | 0.07 | free-settling |
| 8.0 | 36.36 | 0.08 | free-settling |
| 10.0 | 35.70 | 0.09 | free-settling |
| 12.0 | 31.75 | 0.03 | compression |
| 14.0 | 28.42 | 0.04 | compression |
| 16.0 | 25.75 | 0.05 | compression |
| 18.0 | 23.61 | 0.06 | compression |
| 20.0 | 21.89 | 0.07 | compression |
| 22.0 | 20.51 | 0.08 | compression |
| 24.0 | 19.40 | 0.09 | compression |
| 26.0 | 18.51 | 0.03 | compression |
| 28.0 | 17.80 | 0.04 | compression |
| 30.0 | 17.23 | 0.05 | compression |
| 32.0 | 16.77 | 0.06 | compression |
| 34.0 | 16.40 | 0.07 | compression |
| 36.0 | 16.10 | 0.08 | compression |
| 38.0 | 15.86 | 0.09 | compression |
| 40.0 | 15.67 | 0.03 | compression |
| 42.0 | 15.52 | 0.04 | compression |
| 44.0 | 15.40 | 0.05 | compression |
| 46.0 | 15.30 | 0.06 | compression |
| 48.0 | 15.22 | 0.07 | compression |
| 50.0 | 15.16 | 0.08 | compression |
| 52.0 | 15.11 | 0.09 | compression |
| 54.0 | 15.07 | 0.03 | compression |
| 56.0 | 15.03 | 0.04 | compression |
| 58.0 | 15.01 | 0.05 | compression |
| 60.0 | 14.99 | 0.06 | compression |
| 62.0 | 14.97 | 0.07 | compression |
| 64.0 | 14.96 | 0.08 | compression |
| 66.0 | 14.94 | 0.09 | compression |
| 68.0 | 14.94 | 0.03 | compression |
| 70.0 | 14.93 | 0.04 | compression |
| 72.0 | 14.92 | 0.05 | compression |
| 74.0 | 14.92 | 0.06 | compression |
| 76.0 | 14.91 | 0.07 | compression |
| 78.0 | 14.91 | 0.08 | compression |
| 80.0 | 14.91 | 0.09 | compression |
| 82.0 | 14.91 | 0.03 | compression |
| 84.0 | 14.91 | 0.04 | compression |
| 86.0 | 14.90 | 0.05 | compression |
| 88.0 | 14.90 | 0.06 | compression |
| 90.0 | 14.90 | 0.07 | compression |
| 92.0 | 14.90 | 0.08 | compression |
| 94.0 | 14.90 | 0.09 | compression |
| 96.0 | 14.90 | 0.03 | compression |
| 98.0 | 14.90 | 0.04 | compression |
| 100.0 | 14.90 | 0.05 | compression |
| 102.0 | 14.90 | 0.06 | compression |
| 104.0 | 14.90 | 0.07 | compression |
| 106.0 | 14.90 | 0.08 | compression |
| 108.0 | 14.90 | 0.09 | compression |
| 110.0 | 14.90 | 0.03 | compression |
| 112.0 | 14.90 | 0.04 | compression |
| 114.0 | 14.90 | 0.05 | compression |
| 116.0 | 14.90 | 0.06 | compression |
| 118.0 | 14.90 | 0.07 | compression |
| 120.0 | 14.90 | 0.08 | compression |
| 122.0 | 14.90 | 0.09 | compression |
| 124.0 | 14.90 | 0.03 | compression |
| 126.0 | 14.90 | 0.04 | compression |
| 128.0 | 14.90 | 0.05 | compression |
| 130.0 | 14.90 | 0.06 | compression |
| 132.0 | 14.90 | 0.07 | compression |
| 134.0 | 14.90 | 0.08 | compression |
| 136.0 | 14.90 | 0.09 | compression |
| 138.0 | 14.90 | 0.03 | compression |
| 140.0 | 14.90 | 0.04 | compression |
| 142.0 | 14.90 | 0.05 | compression |

The SC-2208 digest shows the breakpoint near 10.1 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2209

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 43.00 | 0.05 | free-settling |
| 2.0 | 42.12 | 0.06 | free-settling |
| 4.0 | 41.24 | 0.07 | free-settling |
| 6.0 | 38.42 | 0.08 | compression |
| 8.0 | 32.45 | 0.09 | compression |
| 10.0 | 28.11 | 0.03 | compression |
| 12.0 | 24.96 | 0.04 | compression |
| 14.0 | 22.67 | 0.05 | compression |
| 16.0 | 21.01 | 0.06 | compression |
| 18.0 | 19.80 | 0.07 | compression |
| 20.0 | 18.92 | 0.08 | compression |
| 22.0 | 18.29 | 0.09 | compression |
| 24.0 | 17.83 | 0.03 | compression |
| 26.0 | 17.49 | 0.04 | compression |
| 28.0 | 17.25 | 0.05 | compression |
| 30.0 | 17.07 | 0.06 | compression |
| 32.0 | 16.94 | 0.07 | compression |
| 34.0 | 16.85 | 0.08 | compression |
| 36.0 | 16.78 | 0.09 | compression |
| 38.0 | 16.73 | 0.03 | compression |
| 40.0 | 16.69 | 0.04 | compression |
| 42.0 | 16.67 | 0.05 | compression |
| 44.0 | 16.65 | 0.06 | compression |
| 46.0 | 16.64 | 0.07 | compression |
| 48.0 | 16.63 | 0.08 | compression |
| 50.0 | 16.62 | 0.09 | compression |
| 52.0 | 16.61 | 0.03 | compression |
| 54.0 | 16.61 | 0.04 | compression |
| 56.0 | 16.61 | 0.05 | compression |
| 58.0 | 16.61 | 0.06 | compression |
| 60.0 | 16.60 | 0.07 | compression |
| 62.0 | 16.60 | 0.08 | compression |
| 64.0 | 16.60 | 0.09 | compression |
| 66.0 | 16.60 | 0.03 | compression |
| 68.0 | 16.60 | 0.04 | compression |
| 70.0 | 16.60 | 0.05 | compression |
| 72.0 | 16.60 | 0.06 | compression |
| 74.0 | 16.60 | 0.07 | compression |
| 76.0 | 16.60 | 0.08 | compression |
| 78.0 | 16.60 | 0.09 | compression |
| 80.0 | 16.60 | 0.03 | compression |
| 82.0 | 16.60 | 0.04 | compression |
| 84.0 | 16.60 | 0.05 | compression |
| 86.0 | 16.60 | 0.06 | compression |
| 88.0 | 16.60 | 0.07 | compression |
| 90.0 | 16.60 | 0.08 | compression |
| 92.0 | 16.60 | 0.09 | compression |
| 94.0 | 16.60 | 0.03 | compression |
| 96.0 | 16.60 | 0.04 | compression |
| 98.0 | 16.60 | 0.05 | compression |
| 100.0 | 16.60 | 0.06 | compression |
| 102.0 | 16.60 | 0.07 | compression |
| 104.0 | 16.60 | 0.08 | compression |
| 106.0 | 16.60 | 0.09 | compression |
| 108.0 | 16.60 | 0.03 | compression |
| 110.0 | 16.60 | 0.04 | compression |
| 112.0 | 16.60 | 0.05 | compression |
| 114.0 | 16.60 | 0.06 | compression |
| 116.0 | 16.60 | 0.07 | compression |
| 118.0 | 16.60 | 0.08 | compression |
| 120.0 | 16.60 | 0.09 | compression |
| 122.0 | 16.60 | 0.03 | compression |
| 124.0 | 16.60 | 0.04 | compression |
| 126.0 | 16.60 | 0.05 | compression |
| 128.0 | 16.60 | 0.06 | compression |
| 130.0 | 16.60 | 0.07 | compression |
| 132.0 | 16.60 | 0.08 | compression |
| 134.0 | 16.60 | 0.09 | compression |
| 136.0 | 16.60 | 0.03 | compression |
| 138.0 | 16.60 | 0.04 | compression |
| 140.0 | 16.60 | 0.05 | compression |
| 142.0 | 16.60 | 0.06 | compression |

The SC-2209 digest shows the breakpoint near 5.4 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2210

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 40.50 | 0.06 | free-settling |
| 2.0 | 39.40 | 0.07 | free-settling |
| 4.0 | 38.30 | 0.08 | free-settling |
| 6.0 | 37.20 | 0.09 | free-settling |
| 8.0 | 34.51 | 0.03 | compression |
| 10.0 | 31.35 | 0.04 | compression |
| 12.0 | 28.60 | 0.05 | compression |
| 14.0 | 26.21 | 0.06 | compression |
| 16.0 | 24.13 | 0.07 | compression |
| 18.0 | 22.32 | 0.08 | compression |
| 20.0 | 20.75 | 0.09 | compression |
| 22.0 | 19.39 | 0.03 | compression |
| 24.0 | 18.20 | 0.04 | compression |
| 26.0 | 17.17 | 0.05 | compression |
| 28.0 | 16.27 | 0.06 | compression |
| 30.0 | 15.49 | 0.07 | compression |
| 32.0 | 14.81 | 0.08 | compression |
| 34.0 | 14.22 | 0.09 | compression |
| 36.0 | 13.71 | 0.03 | compression |
| 38.0 | 13.26 | 0.04 | compression |
| 40.0 | 12.88 | 0.05 | compression |
| 42.0 | 12.54 | 0.06 | compression |
| 44.0 | 12.25 | 0.07 | compression |
| 46.0 | 11.99 | 0.08 | compression |
| 48.0 | 11.77 | 0.09 | compression |
| 50.0 | 11.58 | 0.03 | compression |
| 52.0 | 11.41 | 0.04 | compression |
| 54.0 | 11.27 | 0.05 | compression |
| 56.0 | 11.14 | 0.06 | compression |
| 58.0 | 11.03 | 0.07 | compression |
| 60.0 | 10.94 | 0.08 | compression |
| 62.0 | 10.85 | 0.09 | compression |
| 64.0 | 10.78 | 0.03 | compression |
| 66.0 | 10.72 | 0.04 | compression |
| 68.0 | 10.66 | 0.05 | compression |
| 70.0 | 10.62 | 0.06 | compression |
| 72.0 | 10.57 | 0.07 | compression |
| 74.0 | 10.54 | 0.08 | compression |
| 76.0 | 10.51 | 0.09 | compression |
| 78.0 | 10.48 | 0.03 | compression |
| 80.0 | 10.46 | 0.04 | compression |
| 82.0 | 10.44 | 0.05 | compression |
| 84.0 | 10.42 | 0.06 | compression |
| 86.0 | 10.40 | 0.07 | compression |
| 88.0 | 10.39 | 0.08 | compression |
| 90.0 | 10.38 | 0.09 | compression |
| 92.0 | 10.37 | 0.03 | compression |
| 94.0 | 10.36 | 0.04 | compression |
| 96.0 | 10.35 | 0.05 | compression |
| 98.0 | 10.34 | 0.06 | compression |
| 100.0 | 10.34 | 0.07 | compression |
| 102.0 | 10.33 | 0.08 | compression |
| 104.0 | 10.33 | 0.09 | compression |
| 106.0 | 10.33 | 0.03 | compression |
| 108.0 | 10.32 | 0.04 | compression |
| 110.0 | 10.32 | 0.05 | compression |
| 112.0 | 10.32 | 0.06 | compression |
| 114.0 | 10.31 | 0.07 | compression |
| 116.0 | 10.31 | 0.08 | compression |
| 118.0 | 10.31 | 0.09 | compression |
| 120.0 | 10.31 | 0.03 | compression |
| 122.0 | 10.31 | 0.04 | compression |
| 124.0 | 10.31 | 0.05 | compression |
| 126.0 | 10.31 | 0.06 | compression |
| 128.0 | 10.31 | 0.07 | compression |
| 130.0 | 10.30 | 0.08 | compression |
| 132.0 | 10.30 | 0.09 | compression |
| 134.0 | 10.30 | 0.03 | compression |
| 136.0 | 10.30 | 0.04 | compression |
| 138.0 | 10.30 | 0.05 | compression |
| 140.0 | 10.30 | 0.06 | compression |
| 142.0 | 10.30 | 0.07 | compression |

The SC-2210 digest shows the breakpoint near 6.7 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2211

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 46.00 | 0.07 | free-settling |
| 2.0 | 44.68 | 0.08 | free-settling |
| 4.0 | 43.36 | 0.09 | free-settling |
| 6.0 | 42.04 | 0.03 | free-settling |
| 8.0 | 40.72 | 0.04 | free-settling |
| 10.0 | 34.59 | 0.05 | compression |
| 12.0 | 29.77 | 0.06 | compression |
| 14.0 | 25.98 | 0.07 | compression |
| 16.0 | 23.00 | 0.08 | compression |
| 18.0 | 20.65 | 0.09 | compression |
| 20.0 | 18.80 | 0.03 | compression |
| 22.0 | 17.35 | 0.04 | compression |
| 24.0 | 16.21 | 0.05 | compression |
| 26.0 | 15.31 | 0.06 | compression |
| 28.0 | 14.61 | 0.07 | compression |
| 30.0 | 14.05 | 0.08 | compression |
| 32.0 | 13.61 | 0.09 | compression |
| 34.0 | 13.27 | 0.03 | compression |
| 36.0 | 13.00 | 0.04 | compression |
| 38.0 | 12.78 | 0.05 | compression |
| 40.0 | 12.62 | 0.06 | compression |
| 42.0 | 12.49 | 0.07 | compression |
| 44.0 | 12.38 | 0.08 | compression |
| 46.0 | 12.30 | 0.09 | compression |
| 48.0 | 12.24 | 0.03 | compression |
| 50.0 | 12.19 | 0.04 | compression |
| 52.0 | 12.15 | 0.05 | compression |
| 54.0 | 12.12 | 0.06 | compression |
| 56.0 | 12.09 | 0.07 | compression |
| 58.0 | 12.07 | 0.08 | compression |
| 60.0 | 12.06 | 0.09 | compression |
| 62.0 | 12.04 | 0.03 | compression |
| 64.0 | 12.03 | 0.04 | compression |
| 66.0 | 12.03 | 0.05 | compression |
| 68.0 | 12.02 | 0.06 | compression |
| 70.0 | 12.02 | 0.07 | compression |
| 72.0 | 12.01 | 0.08 | compression |
| 74.0 | 12.01 | 0.09 | compression |
| 76.0 | 12.01 | 0.03 | compression |
| 78.0 | 12.01 | 0.04 | compression |
| 80.0 | 12.01 | 0.05 | compression |
| 82.0 | 12.00 | 0.06 | compression |
| 84.0 | 12.00 | 0.07 | compression |
| 86.0 | 12.00 | 0.08 | compression |
| 88.0 | 12.00 | 0.09 | compression |
| 90.0 | 12.00 | 0.03 | compression |
| 92.0 | 12.00 | 0.04 | compression |
| 94.0 | 12.00 | 0.05 | compression |
| 96.0 | 12.00 | 0.06 | compression |
| 98.0 | 12.00 | 0.07 | compression |
| 100.0 | 12.00 | 0.08 | compression |
| 102.0 | 12.00 | 0.09 | compression |
| 104.0 | 12.00 | 0.03 | compression |
| 106.0 | 12.00 | 0.04 | compression |
| 108.0 | 12.00 | 0.05 | compression |
| 110.0 | 12.00 | 0.06 | compression |
| 112.0 | 12.00 | 0.07 | compression |
| 114.0 | 12.00 | 0.08 | compression |
| 116.0 | 12.00 | 0.09 | compression |
| 118.0 | 12.00 | 0.03 | compression |
| 120.0 | 12.00 | 0.04 | compression |
| 122.0 | 12.00 | 0.05 | compression |
| 124.0 | 12.00 | 0.06 | compression |
| 126.0 | 12.00 | 0.07 | compression |
| 128.0 | 12.00 | 0.08 | compression |
| 130.0 | 12.00 | 0.09 | compression |
| 132.0 | 12.00 | 0.03 | compression |
| 134.0 | 12.00 | 0.04 | compression |
| 136.0 | 12.00 | 0.05 | compression |
| 138.0 | 12.00 | 0.06 | compression |
| 140.0 | 12.00 | 0.07 | compression |
| 142.0 | 12.00 | 0.08 | compression |

The SC-2211 digest shows the breakpoint near 8.0 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

### Digest — SC-2212

| t (s) | mean H (cm) | sd (cm) | phase |
|-------|-------------|---------|-------|
| 0.0 | 42.50 | 0.08 | free-settling |
| 2.0 | 40.96 | 0.09 | free-settling |
| 4.0 | 39.42 | 0.03 | free-settling |
| 6.0 | 37.88 | 0.04 | free-settling |
| 8.0 | 36.34 | 0.05 | free-settling |
| 10.0 | 32.91 | 0.06 | compression |
| 12.0 | 27.37 | 0.07 | compression |
| 14.0 | 23.43 | 0.08 | compression |
| 16.0 | 20.63 | 0.09 | compression |
| 18.0 | 18.63 | 0.03 | compression |
| 20.0 | 17.21 | 0.04 | compression |
| 22.0 | 16.20 | 0.05 | compression |
| 24.0 | 15.48 | 0.06 | compression |
| 26.0 | 14.97 | 0.07 | compression |
| 28.0 | 14.60 | 0.08 | compression |
| 30.0 | 14.34 | 0.09 | compression |
| 32.0 | 14.16 | 0.03 | compression |
| 34.0 | 14.02 | 0.04 | compression |
| 36.0 | 13.93 | 0.05 | compression |
| 38.0 | 13.86 | 0.06 | compression |
| 40.0 | 13.82 | 0.07 | compression |
| 42.0 | 13.78 | 0.08 | compression |
| 44.0 | 13.76 | 0.09 | compression |
| 46.0 | 13.74 | 0.03 | compression |
| 48.0 | 13.73 | 0.04 | compression |
| 50.0 | 13.72 | 0.05 | compression |
| 52.0 | 13.72 | 0.06 | compression |
| 54.0 | 13.71 | 0.07 | compression |
| 56.0 | 13.71 | 0.08 | compression |
| 58.0 | 13.71 | 0.09 | compression |
| 60.0 | 13.70 | 0.03 | compression |
| 62.0 | 13.70 | 0.04 | compression |
| 64.0 | 13.70 | 0.05 | compression |
| 66.0 | 13.70 | 0.06 | compression |
| 68.0 | 13.70 | 0.07 | compression |
| 70.0 | 13.70 | 0.08 | compression |
| 72.0 | 13.70 | 0.09 | compression |
| 74.0 | 13.70 | 0.03 | compression |
| 76.0 | 13.70 | 0.04 | compression |
| 78.0 | 13.70 | 0.05 | compression |
| 80.0 | 13.70 | 0.06 | compression |
| 82.0 | 13.70 | 0.07 | compression |
| 84.0 | 13.70 | 0.08 | compression |
| 86.0 | 13.70 | 0.09 | compression |
| 88.0 | 13.70 | 0.03 | compression |
| 90.0 | 13.70 | 0.04 | compression |
| 92.0 | 13.70 | 0.05 | compression |
| 94.0 | 13.70 | 0.06 | compression |
| 96.0 | 13.70 | 0.07 | compression |
| 98.0 | 13.70 | 0.08 | compression |
| 100.0 | 13.70 | 0.09 | compression |
| 102.0 | 13.70 | 0.03 | compression |
| 104.0 | 13.70 | 0.04 | compression |
| 106.0 | 13.70 | 0.05 | compression |
| 108.0 | 13.70 | 0.06 | compression |
| 110.0 | 13.70 | 0.07 | compression |
| 112.0 | 13.70 | 0.08 | compression |
| 114.0 | 13.70 | 0.09 | compression |
| 116.0 | 13.70 | 0.03 | compression |
| 118.0 | 13.70 | 0.04 | compression |
| 120.0 | 13.70 | 0.05 | compression |
| 122.0 | 13.70 | 0.06 | compression |
| 124.0 | 13.70 | 0.07 | compression |
| 126.0 | 13.70 | 0.08 | compression |
| 128.0 | 13.70 | 0.09 | compression |
| 130.0 | 13.70 | 0.03 | compression |
| 132.0 | 13.70 | 0.04 | compression |
| 134.0 | 13.70 | 0.05 | compression |
| 136.0 | 13.70 | 0.06 | compression |
| 138.0 | 13.70 | 0.07 | compression |
| 140.0 | 13.70 | 0.08 | compression |
| 142.0 | 13.70 | 0.09 | compression |

The SC-2212 digest shows the breakpoint near 9.3 s separating the two regimes. The standard deviations are the replicate spread and are consistent with the §14 uncertainty budget. These tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition channels from the serving layer and converts them per §5 and §8.

## Appendix A — Units and Constants (non-binding)

Standard gravity is `9.80665 m/s²`; for routine reduction the rounded value `g = 9.81 m/s²` from §8 is used. 1 cm = 10 mm; 1 Pa·s = 1000 cP. Times may incidentally be quoted in minutes in older logbooks (1 min = 60000 ms); the acquisition channel used here is in milliseconds (§8). Dynamic viscosity of water near room temperature is approximately 1.0 mPa·s but the analysis uses the database value for the experiment, not this nominal figure.

| quantity | symbol | value | note |
|----------|--------|-------|------|
| standard gravity | g_n | 9.80665 m/s² | rounded to 9.81 in §8 for this reduction |
| reduction gravity | g | 9.81 m/s² | the value used (see §8) |
| ms per second | — | 1000 | time conversion used (§8) |
| ms per minute | — | 60000 | logbook context only; not used |
| cP per Pa·s | — | 1000 | viscosity unit conversion |
| 95% Gaussian factor | z | 1.96 | coverage factor used (§9.4) |
| 99% Gaussian factor | z | 2.576 | reference only |
| legacy coverage factor | k | 2.0 | Revisions A/B; superseded |

## Appendix B — Deprecated Parameter Defaults (non-binding)

Historical optimiser defaults retained for traceability: initial `v1 = 0.5 cm/s`, initial `k = 0.10 1/s`, evaluation cap `5000`, coverage factor `2.0`, minimum points per side `3`, single-exponential model. None of these are the Revision C operative settings; see §9.

## Appendix C — Worked Examples for Other Experiments (illustrative)

The following sketches illustrate the analysis on experiments other than the one governed by this practice. All numbers are illustrative and pertain to the named experiment and its own starting guesses; none is the configuration for experiment 7.

*SC-2201.* An operator obtained a breakpoint near 7.2 s with `v1 ≈ 0.42 cm/s`, `h_inf ≈ 12.1 cm`, and `k ≈ 0.08 1/s`. These values characterise SC-2201 and are not transferable to another experiment.

*SC-2204.* An operator obtained a breakpoint near 9.0 s with `v1 ≈ 0.50 cm/s`, `h_inf ≈ 11.0 cm`, and `k ≈ 0.10 1/s`. These values characterise SC-2204 and are not transferable to another experiment.

*SC-2206.* An operator obtained a breakpoint near 5.5 s with `v1 ≈ 0.61 cm/s`, `h_inf ≈ 16.4 cm`, and `k ≈ 0.14 1/s`. These values characterise SC-2206 and are not transferable to another experiment.

*SC-2210.* An operator obtained a breakpoint near 8.1 s with `v1 ≈ 0.47 cm/s`, `h_inf ≈ 13.0 cm`, and `k ≈ 0.09 1/s`. These values characterise SC-2210 and are not transferable to another experiment.

*SC-2212.* An operator obtained a breakpoint near 6.8 s with `v1 ≈ 0.53 cm/s`, `h_inf ≈ 12.7 cm`, and `k ≈ 0.11 1/s`. These values characterise SC-2212 and are not transferable to another experiment.

## Appendix D — Symbols

- `H(t)` — interface height as a function of time, cm
- `H0` — initial (column) height, cm
- `t_c` — breakpoint time, s
- `v1` — initial settling velocity, cm/s
- `h_inf` — final bed height, cm
- `k` — compression rate constant, 1/s
- `mu` — fluid dynamic viscosity, Pa·s
- `rho_p` — particle density, kg/m³
- `rho_f` — fluid density, kg/m³
- `g` — gravitational acceleration, m/s²
- `d` — effective (Stokes-equivalent) diameter, µm
- `z` — coverage factor for confidence intervals

## Appendix E — Bibliography

1. Coe, H. S., and Clevenger, G. H. (1916). Methods for determining the capacities of slime-settling tanks.
2. Kynch, G. J. (1952). A theory of sedimentation. Trans. Faraday Soc.
3. Richardson, J. F., and Zaki, W. N. (1954). Sedimentation and fluidisation.
4. Fitch, B. (1962). Sedimentation process fundamentals.
5. Talmage, W. P., and Fitch, E. B. (1955). Determining thickener unit areas.
6. Bustos, M. C., Concha, F., Bürger, R., and Tory, E. M. (1999). Sedimentation and Thickening.
7. ISO 13317-1 (2001). Gravitational liquid sedimentation methods.
8. ISO/IEC Guide 98-3 (2008). Uncertainty of measurement (GUM).
9. Meridian Sedimentation Laboratory (2019). MSL-SP-118 Revision A.
10. Meridian Sedimentation Laboratory (2022). MSL-SP-118 Revision B.

## Appendix F — Sensor Calibration Histories (non-binding)

Each probe carries a dated calibration history under MSL-SP-101. Representative histories are reproduced here for context. The authoritative constants for an analysis are those attached to the experiment's assigned sensor in the database (§5), not these historical entries.

### ColumnProbe CP-04 — serial CP04-7781

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.00496 | +0.090 | RL-100 | A. Okafor |
| 2021-07-09 | 0.00498 | +0.095 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.00500 | +0.100 | RL-102 | R. Haddad |
| 2022-07-11 | 0.00502 | +0.105 | RL-103 | M. Sato |
| 2023-01-20 | 0.00504 | +0.110 | RL-104 | A. Okafor |
| 2023-07-14 | 0.00506 | +0.115 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.00508 | +0.120 | RL-106 | R. Haddad |
| 2024-07-11 | 0.00510 | +0.125 | RL-107 | M. Sato |
| 2025-01-20 | 0.00512 | +0.130 | RL-108 | A. Okafor |
| 2025-07-14 | 0.00514 | +0.135 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.00516 | +0.140 | RL-110 | R. Haddad |
| 2026-03-18 | 0.00518 | +0.145 | RL-111 | M. Sato |

The current record for CP04-7781 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-06 — serial CP06-3120

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.00746 | +0.040 | RL-100 | A. Okafor |
| 2021-07-09 | 0.00748 | +0.045 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.00750 | +0.050 | RL-102 | R. Haddad |
| 2022-07-11 | 0.00752 | +0.055 | RL-103 | M. Sato |
| 2023-01-20 | 0.00754 | +0.060 | RL-104 | A. Okafor |
| 2023-07-14 | 0.00756 | +0.065 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.00758 | +0.070 | RL-106 | R. Haddad |
| 2024-07-11 | 0.00760 | +0.075 | RL-107 | M. Sato |
| 2025-01-20 | 0.00762 | +0.080 | RL-108 | A. Okafor |
| 2025-07-14 | 0.00764 | +0.085 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.00766 | +0.090 | RL-110 | R. Haddad |
| 2026-03-18 | 0.00768 | +0.095 | RL-111 | M. Sato |

The current record for CP06-3120 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-08 — serial CP08-9904

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.00996 | -0.010 | RL-100 | A. Okafor |
| 2021-07-09 | 0.00998 | -0.005 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.01000 | +0.000 | RL-102 | R. Haddad |
| 2022-07-11 | 0.01002 | +0.005 | RL-103 | M. Sato |
| 2023-01-20 | 0.01004 | +0.010 | RL-104 | A. Okafor |
| 2023-07-14 | 0.01006 | +0.015 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.01008 | +0.020 | RL-106 | R. Haddad |
| 2024-07-11 | 0.01010 | +0.025 | RL-107 | M. Sato |
| 2025-01-20 | 0.01012 | +0.030 | RL-108 | A. Okafor |
| 2025-07-14 | 0.01014 | +0.035 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.01016 | +0.040 | RL-110 | R. Haddad |
| 2026-03-18 | 0.01018 | +0.045 | RL-111 | M. Sato |

The current record for CP08-9904 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-08 — serial CP08-9911

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.00976 | +0.010 | RL-100 | A. Okafor |
| 2021-07-09 | 0.00978 | +0.015 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.00980 | +0.020 | RL-102 | R. Haddad |
| 2022-07-11 | 0.00982 | +0.025 | RL-103 | M. Sato |
| 2023-01-20 | 0.00984 | +0.030 | RL-104 | A. Okafor |
| 2023-07-14 | 0.00986 | +0.035 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.00988 | +0.040 | RL-106 | R. Haddad |
| 2024-07-11 | 0.00990 | +0.045 | RL-107 | M. Sato |
| 2025-01-20 | 0.00992 | +0.050 | RL-108 | A. Okafor |
| 2025-07-14 | 0.00994 | +0.055 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.00996 | +0.060 | RL-110 | R. Haddad |
| 2026-03-18 | 0.00998 | +0.065 | RL-111 | M. Sato |

The current record for CP08-9911 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-10 — serial CP10-2245

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.01246 | -0.060 | RL-100 | A. Okafor |
| 2021-07-09 | 0.01248 | -0.055 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.01250 | -0.050 | RL-102 | R. Haddad |
| 2022-07-11 | 0.01252 | -0.045 | RL-103 | M. Sato |
| 2023-01-20 | 0.01254 | -0.040 | RL-104 | A. Okafor |
| 2023-07-14 | 0.01256 | -0.035 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.01258 | -0.030 | RL-106 | R. Haddad |
| 2024-07-11 | 0.01260 | -0.025 | RL-107 | M. Sato |
| 2025-01-20 | 0.01262 | -0.020 | RL-108 | A. Okafor |
| 2025-07-14 | 0.01264 | -0.015 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.01266 | -0.010 | RL-110 | R. Haddad |
| 2026-03-18 | 0.01268 | -0.005 | RL-111 | M. Sato |

The current record for CP10-2245 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-10 — serial CP10-2251

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.01176 | +0.020 | RL-100 | A. Okafor |
| 2021-07-09 | 0.01178 | +0.025 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.01180 | +0.030 | RL-102 | R. Haddad |
| 2022-07-11 | 0.01182 | +0.035 | RL-103 | M. Sato |
| 2023-01-20 | 0.01184 | +0.040 | RL-104 | A. Okafor |
| 2023-07-14 | 0.01186 | +0.045 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.01188 | +0.050 | RL-106 | R. Haddad |
| 2024-07-11 | 0.01190 | +0.055 | RL-107 | M. Sato |
| 2025-01-20 | 0.01192 | +0.060 | RL-108 | A. Okafor |
| 2025-07-14 | 0.01194 | +0.065 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.01196 | +0.070 | RL-110 | R. Haddad |
| 2026-03-18 | 0.01198 | +0.075 | RL-111 | M. Sato |

The current record for CP10-2251 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-12 — serial CP12-6680

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.01496 | +0.090 | RL-100 | A. Okafor |
| 2021-07-09 | 0.01498 | +0.095 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.01500 | +0.100 | RL-102 | R. Haddad |
| 2022-07-11 | 0.01502 | +0.105 | RL-103 | M. Sato |
| 2023-01-20 | 0.01504 | +0.110 | RL-104 | A. Okafor |
| 2023-07-14 | 0.01506 | +0.115 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.01508 | +0.120 | RL-106 | R. Haddad |
| 2024-07-11 | 0.01510 | +0.125 | RL-107 | M. Sato |
| 2025-01-20 | 0.01512 | +0.130 | RL-108 | A. Okafor |
| 2025-07-14 | 0.01514 | +0.135 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.01516 | +0.140 | RL-110 | R. Haddad |
| 2026-03-18 | 0.01518 | +0.145 | RL-111 | M. Sato |

The current record for CP12-6680 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-12 — serial CP12-6692

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.01466 | +0.070 | RL-100 | A. Okafor |
| 2021-07-09 | 0.01468 | +0.075 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.01470 | +0.080 | RL-102 | R. Haddad |
| 2022-07-11 | 0.01472 | +0.085 | RL-103 | M. Sato |
| 2023-01-20 | 0.01474 | +0.090 | RL-104 | A. Okafor |
| 2023-07-14 | 0.01476 | +0.095 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.01478 | +0.100 | RL-106 | R. Haddad |
| 2024-07-11 | 0.01480 | +0.105 | RL-107 | M. Sato |
| 2025-01-20 | 0.01482 | +0.110 | RL-108 | A. Okafor |
| 2025-07-14 | 0.01484 | +0.115 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.01486 | +0.120 | RL-110 | R. Haddad |
| 2026-03-18 | 0.01488 | +0.125 | RL-111 | M. Sato |

The current record for CP12-6692 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-14 — serial CP14-0034

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.01996 | -0.010 | RL-100 | A. Okafor |
| 2021-07-09 | 0.01998 | -0.005 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.02000 | +0.000 | RL-102 | R. Haddad |
| 2022-07-11 | 0.02002 | +0.005 | RL-103 | M. Sato |
| 2023-01-20 | 0.02004 | +0.010 | RL-104 | A. Okafor |
| 2023-07-14 | 0.02006 | +0.015 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.02008 | +0.020 | RL-106 | R. Haddad |
| 2024-07-11 | 0.02010 | +0.025 | RL-107 | M. Sato |
| 2025-01-20 | 0.02012 | +0.030 | RL-108 | A. Okafor |
| 2025-07-14 | 0.02014 | +0.035 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.02016 | +0.040 | RL-110 | R. Haddad |
| 2026-03-18 | 0.02018 | +0.045 | RL-111 | M. Sato |

The current record for CP14-0034 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-14 — serial CP14-0041

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.01946 | +0.030 | RL-100 | A. Okafor |
| 2021-07-09 | 0.01948 | +0.035 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.01950 | +0.040 | RL-102 | R. Haddad |
| 2022-07-11 | 0.01952 | +0.045 | RL-103 | M. Sato |
| 2023-01-20 | 0.01954 | +0.050 | RL-104 | A. Okafor |
| 2023-07-14 | 0.01956 | +0.055 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.01958 | +0.060 | RL-106 | R. Haddad |
| 2024-07-11 | 0.01960 | +0.065 | RL-107 | M. Sato |
| 2025-01-20 | 0.01962 | +0.070 | RL-108 | A. Okafor |
| 2025-07-14 | 0.01964 | +0.075 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.01966 | +0.080 | RL-110 | R. Haddad |
| 2026-03-18 | 0.01968 | +0.085 | RL-111 | M. Sato |

The current record for CP14-0041 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-16 — serial CP16-5519

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.02496 | -0.110 | RL-100 | A. Okafor |
| 2021-07-09 | 0.02498 | -0.105 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.02500 | -0.100 | RL-102 | R. Haddad |
| 2022-07-11 | 0.02502 | -0.095 | RL-103 | M. Sato |
| 2023-01-20 | 0.02504 | -0.090 | RL-104 | A. Okafor |
| 2023-07-14 | 0.02506 | -0.085 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.02508 | -0.080 | RL-106 | R. Haddad |
| 2024-07-11 | 0.02510 | -0.075 | RL-107 | M. Sato |
| 2025-01-20 | 0.02512 | -0.070 | RL-108 | A. Okafor |
| 2025-07-14 | 0.02514 | -0.065 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.02516 | -0.060 | RL-110 | R. Haddad |
| 2026-03-18 | 0.02518 | -0.055 | RL-111 | M. Sato |

The current record for CP16-5519 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-16 — serial CP16-5527

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.02436 | +0.050 | RL-100 | A. Okafor |
| 2021-07-09 | 0.02438 | +0.055 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.02440 | +0.060 | RL-102 | R. Haddad |
| 2022-07-11 | 0.02442 | +0.065 | RL-103 | M. Sato |
| 2023-01-20 | 0.02444 | +0.070 | RL-104 | A. Okafor |
| 2023-07-14 | 0.02446 | +0.075 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.02448 | +0.080 | RL-106 | R. Haddad |
| 2024-07-11 | 0.02450 | +0.085 | RL-107 | M. Sato |
| 2025-01-20 | 0.02452 | +0.090 | RL-108 | A. Okafor |
| 2025-07-14 | 0.02454 | +0.095 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.02456 | +0.100 | RL-110 | R. Haddad |
| 2026-03-18 | 0.02458 | +0.105 | RL-111 | M. Sato |

The current record for CP16-5527 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-18 — serial CP18-7702

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.02996 | -0.010 | RL-100 | A. Okafor |
| 2021-07-09 | 0.02998 | -0.005 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.03000 | +0.000 | RL-102 | R. Haddad |
| 2022-07-11 | 0.03002 | +0.005 | RL-103 | M. Sato |
| 2023-01-20 | 0.03004 | +0.010 | RL-104 | A. Okafor |
| 2023-07-14 | 0.03006 | +0.015 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.03008 | +0.020 | RL-106 | R. Haddad |
| 2024-07-11 | 0.03010 | +0.025 | RL-107 | M. Sato |
| 2025-01-20 | 0.03012 | +0.030 | RL-108 | A. Okafor |
| 2025-07-14 | 0.03014 | +0.035 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.03016 | +0.040 | RL-110 | R. Haddad |
| 2026-03-18 | 0.03018 | +0.045 | RL-111 | M. Sato |

The current record for CP18-7702 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-18 — serial CP18-7719

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.02956 | +0.040 | RL-100 | A. Okafor |
| 2021-07-09 | 0.02958 | +0.045 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.02960 | +0.050 | RL-102 | R. Haddad |
| 2022-07-11 | 0.02962 | +0.055 | RL-103 | M. Sato |
| 2023-01-20 | 0.02964 | +0.060 | RL-104 | A. Okafor |
| 2023-07-14 | 0.02966 | +0.065 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.02968 | +0.070 | RL-106 | R. Haddad |
| 2024-07-11 | 0.02970 | +0.075 | RL-107 | M. Sato |
| 2025-01-20 | 0.02972 | +0.080 | RL-108 | A. Okafor |
| 2025-07-14 | 0.02974 | +0.085 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.02976 | +0.090 | RL-110 | R. Haddad |
| 2026-03-18 | 0.02978 | +0.095 | RL-111 | M. Sato |

The current record for CP18-7719 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-20 — serial CP20-1188

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.03996 | +0.090 | RL-100 | A. Okafor |
| 2021-07-09 | 0.03998 | +0.095 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.04000 | +0.100 | RL-102 | R. Haddad |
| 2022-07-11 | 0.04002 | +0.105 | RL-103 | M. Sato |
| 2023-01-20 | 0.04004 | +0.110 | RL-104 | A. Okafor |
| 2023-07-14 | 0.04006 | +0.115 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.04008 | +0.120 | RL-106 | R. Haddad |
| 2024-07-11 | 0.04010 | +0.125 | RL-107 | M. Sato |
| 2025-01-20 | 0.04012 | +0.130 | RL-108 | A. Okafor |
| 2025-07-14 | 0.04014 | +0.135 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.04016 | +0.140 | RL-110 | R. Haddad |
| 2026-03-18 | 0.04018 | +0.145 | RL-111 | M. Sato |

The current record for CP20-1188 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

### ColumnProbe CP-20 — serial CP20-1196

| date | raw_scale | raw_offset | reference standard | technician |
|------|-----------|------------|--------------------|------------|
| 2021-01-12 | 0.03916 | +0.060 | RL-100 | A. Okafor |
| 2021-07-09 | 0.03918 | +0.065 | RL-101 | L. Bianchi |
| 2022-01-15 | 0.03920 | +0.070 | RL-102 | R. Haddad |
| 2022-07-11 | 0.03922 | +0.075 | RL-103 | M. Sato |
| 2023-01-20 | 0.03924 | +0.080 | RL-104 | A. Okafor |
| 2023-07-14 | 0.03926 | +0.085 | RL-105 | L. Bianchi |
| 2024-01-15 | 0.03928 | +0.090 | RL-106 | R. Haddad |
| 2024-07-11 | 0.03930 | +0.095 | RL-107 | M. Sato |
| 2025-01-20 | 0.03932 | +0.100 | RL-108 | A. Okafor |
| 2025-07-14 | 0.03934 | +0.105 | RL-109 | L. Bianchi |
| 2025-12-02 | 0.03936 | +0.110 | RL-110 | R. Haddad |
| 2026-03-18 | 0.03938 | +0.115 | RL-111 | M. Sato |

The current record for CP20-1196 is the most recent entry above. The probe is recalibrated every six months; intermediate drift is within the calibration uncertainty of §14. None of these entries is the withdrawn laboratory-wide constant.

## Appendix G — Commentary on Each Governing Parameter (non-binding)

This appendix collects commentary on each element of the governing configuration. The binding values are stated in §8 and §9; the commentary here explains the rationale and the relationship to the superseded values, and must not itself be read as the configuration.

- **Kinetic model.** The two-phase model captures both the free-settling and compression regimes with a single continuous curve. It replaced the single-exponential Revision A model, which systematically underestimated the initial settling velocity. Governing value: two-phase (§9.1).
- **Breakpoint minimum points per side.** Requiring five points on each side of a candidate breakpoint stabilises the transition-time estimate against noise. Revision B used three, which admitted spurious early breakpoints. Governing value: five (§9.2).
- **Initial velocity guess.** Starting the optimiser at 1.0 cm/s improves convergence for the typical hindered-settling velocities seen in the registry, relative to the 0.5 cm/s used historically. Governing value: 1.0 cm/s (§9.3).
- **Initial rate-constant guess.** Starting k at 0.05 1/s reflects the slower compression observed with the current suspensions, relative to the historical 0.10 1/s. Governing value: 0.05 1/s (§9.3).
- **Final-bed-height initialisation.** The final bed height is started at the minimum observed interface height in all revisions; this is unchanged.
- **Optimiser evaluation cap.** Ten thousand evaluations virtually eliminate the non-convergence seen with the historical 5000 cap on long records. Governing value: 10000 (§9.3).
- **Coverage factor.** A factor of 1.96 yields a 95% Gaussian interval for the large samples typical of settling-column records, replacing the rounded 2.0 of earlier revisions. Governing value: 1.96 (§9.4).
- **Gravitational constant.** The rounded value 9.81 m/s² is sufficient given the dominant calibration and timing uncertainties; the full 9.80665 m/s² is unnecessary here. Governing value: 9.81 m/s² (§8).
- **Time conversion.** Milliseconds are divided by 1000 to obtain seconds. Governing value: divide by 1000 (§8).
- **Diameter unit.** The Stokes-equivalent diameter is reported in micrometres. Governing value: micrometres (§8, §9.5).

