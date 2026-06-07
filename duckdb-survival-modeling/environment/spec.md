# Discrete-Time Survival Modeling — Technical Specification

This document is the binding contract for the survival-modeling pipeline. All table
names, column names, the model configuration, and the metric definitions below are
normative: the verifier reads/writes the same schemas and recomputes the same
quantities. The database is DuckDB at `/app/survival.duckdb`.

## 1. Source data — table `subjects`

One row per study subject. Right-censored clinical follow-up over a fixed grid of
`K = 12` discrete periods (period index `1 … 12`).

| column | type | meaning |
|---|---|---|
| `subject_id` | BIGINT | unique subject identifier |
| `age` | DOUBLE | age in years at baseline |
| `biomarker` | DOUBLE | positive continuous biomarker level |
| `treatment` | INTEGER | treatment arm, `0` = control, `1` = treated |
| `stage` | VARCHAR | disease stage, one of `I`, `II`, `III` |
| `sex` | VARCHAR | `F` or `M` |
| `time_observed` | INTEGER | period of last observation, `1 … K` |
| `event` | INTEGER | `1` if the event occurred at `time_observed`, `0` if censored there |
| `split` | VARCHAR | `train` or `test` (assigned per subject) |

The model is trained on `split = 'train'` and all reported metrics are evaluated on
`split = 'test'`.

## 2. Discrete-time framework

For a subject with covariate vector `x`, the discrete hazard in period `t` is
`h(t | x) = P(event in period t | survived through t-1, x)`. The survival function is
the product of period-wise survival probabilities:

```
S(t | x) = Π_{k=1..t} ( 1 - h(k | x) )
```

The model estimates `h(t | x)` as a logistic regression over person-period rows.

## 3. Milestone 1 — table `person_period`

Expand each subject into one row per period `t = 1 … time_observed` (inclusive). The
binary period outcome `event_in_period` is `1` only in the subject's event period and
`0` otherwise:

```
event_in_period = 1  iff  event = 1 AND period = time_observed,  else 0
```

A censored subject therefore contributes only `0`s. Required schema (baseline
covariates copied unchanged from `subjects`):

| column | type |
|---|---|
| `subject_id` | BIGINT |
| `period` | INTEGER (1 … time_observed) |
| `age` | DOUBLE |
| `biomarker` | DOUBLE |
| `treatment` | INTEGER |
| `stage` | VARCHAR |
| `sex` | VARCHAR |
| `split` | VARCHAR |
| `event_in_period` | INTEGER (0/1) |

The total row count equals `SUM(time_observed)` over all subjects.

## 4. Milestone 2 — discrete-time hazard model

Fit `sklearn.linear_model.LogisticRegression` predicting `event_in_period` from the
following design matrix, built from the **train** person-period rows. Columns, in this
exact construction:

| design column | definition |
|---|---|
| `age` | `age` (unchanged) |
| `log_biomarker` | `ln(biomarker)` (natural log) |
| `treatment` | `treatment` (0/1) |
| `stage_II` | `1` if `stage = 'II'` else `0` |
| `stage_III` | `1` if `stage = 'III'` else `0` |
| `sex_M` | `1` if `sex = 'M'` else `0` |
| `period` | `period` (integer 1 … K, unchanged) |

No feature scaling is applied. Model hyperparameters (all explicit):
`LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs", random_state=42)`.

Serialize the fitted estimator with `joblib` to `/app/artifacts/survival_model.joblib`.
The estimated hazard for any `(x, t)` is `predict_proba(...)[:, 1]` on the design row
for period `t`.

## 5. Milestone 3 — predictions and evaluation (test subjects)

Using the saved model, for every `split = 'test'` subject compute the hazard at each
period `t = 1 … K` and the survival curve `S(t | x)` per §2.

### 5.1 Output tables

`survival_curves` — one row per test subject per period:

| column | type |
|---|---|
| `subject_id` | BIGINT |
| `period` | INTEGER (1 … K) |
| `survival_prob` | DOUBLE (= `S(period | x)`, in `[0, 1]`, non-increasing in period) |

`risk_scores` — one row per test subject:

| column | type |
|---|---|
| `subject_id` | BIGINT |
| `risk_score` | DOUBLE |

where `risk_score = 1 - S(K | x)` (probability of event by the final horizon `K`).

`model_metrics` — one row per metric:

| column | type |
|---|---|
| `metric` | VARCHAR (`c_index`, `integrated_brier_score`) |
| `value` | DOUBLE |

### 5.2 Predictions file

Also write `/app/artifacts/predictions.csv` with header
`subject_id,risk_score,survival_prob_at_K` (one row per test subject; `survival_prob_at_K = S(K | x)`).

### 5.3 Concordance index `c_index` (Harrell, censoring-aware)

Over all ordered pairs `(i, j)` of test subjects, a pair is **comparable** iff subject
`i` has an event (`event_i = 1`) and `time_observed_i < time_observed_j`. A comparable
pair is **concordant** iff `risk_score_i > risk_score_j` and **tied** iff
`risk_score_i = risk_score_j`. Then

```
c_index = ( #concordant + 0.5 · #tied ) / #comparable
```

### 5.4 Integrated Brier Score `integrated_brier_score` (IPCW)

Let `G` be the Kaplan–Meier estimate of the **censoring** survival function on the test
set, obtained by treating a censoring (`event = 0`) as the event of interest: stepping
through the distinct observed times `u` in ascending order, `G(u) = G(prev) · (1 - c_u / n_u)`,
where `c_u` is the number of test subjects censored at `u` and `n_u` is the number with
`time_observed ≥ u`. `G` is a right-continuous step function (`G = 1` before the first
observed time); evaluate `G(s)` as its value at the largest distinct observed time `≤ s`.

For a horizon `t` and test subject `i` with observed time `T_i`, indicator `δ_i`, and
predicted survival `Ŝ_i(t) = S(t | x_i)`, the IPCW Brier score is

```
BS(t) = (1 / N_test) · Σ_i  b_i(t),  where
  b_i(t) = Ŝ_i(t)^2 / G(T_i)          if T_i ≤ t and δ_i = 1
  b_i(t) = (1 - Ŝ_i(t))^2 / G(t)      if T_i > t
  b_i(t) = 0                          if T_i ≤ t and δ_i = 0   (censored before t)
```

The Integrated Brier Score is the simple average over the `K` discrete horizons:

```
integrated_brier_score = (1 / K) · Σ_{t=1..K} BS(t)
```

### 5.3+ Acceptance floors

A correct pipeline on this dataset achieves `c_index ≥ 0.72` and
`integrated_brier_score ≤ 0.18`.
