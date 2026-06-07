# Discrete-Time Competing-Risks Survival Modeling — Technical Specification

Binding contract for the pipeline. All table/column names, the model configuration,
and the metric definitions are normative: the verifier reads/writes the same schemas
and recomputes the same quantities. Database: DuckDB at `/app/survival.duckdb`.
The follow-up grid has `K = 12` discrete periods (`1 … 12`).

## 1. Source data

### Table `subjects` — one row per subject
| column | type | meaning |
|---|---|---|
| `subject_id` | BIGINT | unique identifier |
| `age` | DOUBLE | age at baseline |
| `treatment` | INTEGER | arm, `0` = control, `1` = treated |
| `stage` | VARCHAR | `I`, `II`, or `III` |
| `sex` | VARCHAR | `F` or `M` |
| `time_observed` | INTEGER | period of last observation, `1 … K` |
| `event_type` | INTEGER | `0` = censored, `1` = cause 1 (disease), `2` = cause 2 (competing) |
| `split` | VARCHAR | `train` or `test` |

### Table `measurements` — longitudinal, sparse
| column | type | meaning |
|---|---|---|
| `subject_id` | BIGINT | subject |
| `period` | INTEGER | visit period at which the biomarker was recorded |
| `biomarker` | DOUBLE | positive biomarker value at that visit |

`biomarker` is **time-varying** and **step-constant between visits**. Every subject has
a measurement at period 1. The biomarker that applies in period `t` is the value from
the most recent visit at or before `t` (last-observation-carried-forward, LOCF). For
periods after a subject's last visit, the last value is carried forward.

The model is trained on `split = 'train'` and all metrics are evaluated on `split = 'test'`.

## 2. Discrete-time competing-risks framework

Two causes compete. The cause-specific hazard in period `t` is
`h_c(t | x) = P(event of cause c in period t | event-free through t-1, x)` for `c ∈ {1, 2}`.
Overall (event-free) survival and the cause-`c` cumulative incidence function (CIF) are

```
S(t | x)    = Π_{k=1..t} ( 1 - h_1(k|x) - h_2(k|x) )          (with S(0) = 1)
CIF_c(t|x)  = Σ_{k=1..t} h_c(k|x) · S(k-1 | x)
```

Note `CIF_c` is NOT `1 - S`; it accumulates cause-`c` hazard weighted by survival to the
start of each period. By construction `CIF_1(t) + CIF_2(t) + S(t) = 1`.

## 3. Milestone 1 — table `person_period`

Expand each subject into one row per period `t = 1 … time_observed`. Attach the LOCF
biomarker for period `t` (most recent `measurements` row with `period ≤ t`). The period
outcome is the competing-risks multinomial label:

```
period_outcome = 1  if event_type = 1 and period = time_observed
               = 2  if event_type = 2 and period = time_observed
               = 0  otherwise
```

Required schema:

| column | type |
|---|---|
| `subject_id` | BIGINT |
| `period` | INTEGER |
| `age` | DOUBLE |
| `biomarker` | DOUBLE (LOCF value active in this period) |
| `treatment` | INTEGER |
| `stage` | VARCHAR |
| `sex` | VARCHAR |
| `split` | VARCHAR |
| `period_outcome` | INTEGER (0/1/2) |

Row count equals `SUM(time_observed)` over all subjects.

## 4. Milestone 2 — multinomial discrete-time hazard model

Fit `sklearn.linear_model.LogisticRegression` predicting `period_outcome` (a 3-class
target) from the **train** person-period rows. Design matrix columns, in this exact
construction:

| design column | definition |
|---|---|
| `age` | `age` |
| `log_biomarker` | `ln(biomarker)` (the LOCF value in the row) |
| `treatment` | `treatment` |
| `stage_II` | `1` if `stage = 'II'` else `0` |
| `stage_III` | `1` if `stage = 'III'` else `0` |
| `sex_M` | `1` if `sex = 'M'` else `0` |
| `period` | `period` |

No feature scaling. Hyperparameters (explicit):
`LogisticRegression(C=1.0, max_iter=5000, solver="lbfgs", tol=1e-8, random_state=42)`.
With three classes this fits a multinomial model. (The tight `tol` makes the fit
converge to the unique optimum so results are reproducible regardless of row order.) Serialize the fitted estimator with
`joblib` to `/app/artifacts/survival_model.joblib`. For a design row, `predict_proba`
returns probabilities ordered by `classes_` (`[0, 1, 2]`); the cause-specific hazards are
`h_1 = P(class 1)` and `h_2 = P(class 2)`.

## 5. Milestone 3 — CIFs, risk scores, evaluation (test subjects)

For every `split = 'test'` subject, score all periods `t = 1 … K` (a full grid up to `K`,
carrying the LOCF biomarker forward past the last visit), compute `h_1(t)`, `h_2(t)`, then
`S(t)`, `CIF_1(t)`, `CIF_2(t)` per §2.

### 5.1 Output tables

`cif_curves` — one row per test subject per period:

| column | type |
|---|---|
| `subject_id` | BIGINT |
| `period` | INTEGER (1 … K) |
| `cif1` | DOUBLE (`CIF_1(period)`, non-decreasing in period) |
| `cif2` | DOUBLE (`CIF_2(period)`, non-decreasing) |
| `survival_prob` | DOUBLE (`S(period)`, non-increasing; `cif1+cif2+survival_prob = 1`) |

`risk_scores` — one row per test subject, `risk_score = CIF_1(K | x)`:

| column | type |
|---|---|
| `subject_id` | BIGINT |
| `risk_score` | DOUBLE |

`model_metrics` — one row per metric (`c_index`, `integrated_brier_score`):

| column | type |
|---|---|
| `metric` | VARCHAR |
| `value` | DOUBLE |

### 5.2 Predictions file

Write `/app/artifacts/predictions.csv` with header
`subject_id,cif1_at_K,cif2_at_K,survival_prob_at_K` (one row per test subject; the three
values are `CIF_1(K)`, `CIF_2(K)`, `S(K)`).

### 5.3 Cause-1 concordance `c_index`

Over ordered pairs `(i, j)` of test subjects, a pair is **comparable** iff subject `i` had
a cause-1 event (`event_type_i = 1`) and `time_observed_i < time_observed_j`. It is
**concordant** iff `risk_score_i > risk_score_j` and **tied** iff equal. Then

```
c_index = ( #concordant + 0.5 · #tied ) / #comparable
```

### 5.4 Cause-1 Integrated Brier Score `integrated_brier_score` (IPCW)

Let `G` be the Kaplan–Meier estimate of the **censoring** survival function on the test set
(treat `event_type = 0` as the event): stepping through distinct observed times `u` ascending,
`G(u) = G(prev) · (1 - c_u / n_u)` where `c_u` = #subjects with `event_type = 0` at `u` and
`n_u` = #subjects with `time_observed ≥ u`. `G` is right-continuous (`G = 1` before the first
time); evaluate `G(s)` as its value at the largest distinct observed time `≤ s`.

For horizon `t` and test subject `i` with observed time `T_i`, `event_type` `δ_i`, and predicted
`CIF_1,i(t)`:

```
BS(t) = (1 / N_test) · Σ_i  b_i(t),  where
  b_i(t) = (CIF_1,i(t) - 1)^2 / G(T_i)   if T_i ≤ t and δ_i = 1
  b_i(t) = (CIF_1,i(t))^2     / G(T_i)   if T_i ≤ t and δ_i = 2
  b_i(t) = (CIF_1,i(t))^2     / G(t)     if T_i > t
  b_i(t) = 0                             if T_i ≤ t and δ_i = 0   (censored before t)
```

```
integrated_brier_score = (1 / K) · Σ_{t=1..K} BS(t)
```

### 5.5 Acceptance floors

A correct pipeline achieves `c_index ≥ 0.62` and `integrated_brier_score ≤ 0.18`. The saved
model must also reproduce the written `cif_curves` when reloaded.
