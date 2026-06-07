"""Generate the synthetic clinical time-to-event dataset into a DuckDB fixture.

Each subject has baseline covariates and is followed over K discrete periods. A
discrete-time hazard h(t|x) = sigmoid(gamma_t + beta·x) drives events; random
dropout plus administrative censoring at K produce right-censored observations.
The resulting `subjects` table (covariates + observed interval + event + split)
is what milestone 1's person-period expansion is built from.
"""

import numpy as np
import pandas as pd
import duckdb

RNG = np.random.default_rng(20240131)
N = 3000
K = 12  # number of discrete follow-up periods (e.g. months)

# baseline per-period hazard offset (gamma_t): mild non-monotone shape
gamma = np.array([-3.1, -3.0, -2.9, -2.85, -2.8, -2.8, -2.75, -2.7, -2.7, -2.65, -2.6, -2.55])

# ---- baseline covariates ----
age = np.clip(RNG.normal(61, 11, N), 30, 90).round(1)
biomarker = np.clip(np.exp(RNG.normal(1.1, 0.5, N)), 0.3, 20).round(3)  # right-skewed
treatment = RNG.integers(0, 2, N)  # 0 = control, 1 = treated
stage = RNG.choice(["I", "II", "III"], size=N, p=[0.4, 0.38, 0.22])
sex = RNG.choice(["F", "M"], size=N, p=[0.5, 0.5])

age_z = (age - 61) / 11
bio_z = (np.log(biomarker) - 1.1) / 0.5
stage_eff = np.select([stage == "I", stage == "II", stage == "III"], [0.0, 0.55, 1.15])
sex_eff = np.where(sex == "M", 0.12, 0.0)

# linear predictor (higher -> higher hazard); treatment is protective
lp = 0.55 * age_z + 0.7 * bio_z - 0.8 * treatment + stage_eff + sex_eff


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


time_observed = np.zeros(N, dtype=int)
event = np.zeros(N, dtype=int)

for i in range(N):
    # event time from sequential discrete hazards
    event_t = K + 1
    for t in range(1, K + 1):
        if RNG.random() < sigmoid(gamma[t - 1] + lp[i]):
            event_t = t
            break
    # random dropout censoring: geometric-ish, else administrative at K
    drop_t = K + 1
    for t in range(1, K + 1):
        if RNG.random() < 0.03:
            drop_t = t
            break
    censor_t = min(drop_t, K)
    if event_t <= censor_t:
        time_observed[i] = event_t
        event[i] = 1
    else:
        time_observed[i] = censor_t
        event[i] = 0

# subject-level train/test split (~70/30), seeded
split = np.where(RNG.random(N) < 0.70, "train", "test")

df = pd.DataFrame(
    {
        "subject_id": np.arange(1, N + 1),
        "age": age,
        "biomarker": biomarker,
        "treatment": treatment.astype(int),
        "stage": stage,
        "sex": sex,
        "time_observed": time_observed,
        "event": event,
        "split": split,
    }
)

if __name__ == "__main__":
    con = duckdb.connect("survival.duckdb")
    con.execute("DROP TABLE IF EXISTS subjects")
    con.execute("CREATE TABLE subjects AS SELECT * FROM df")
    con.close()
    print("rows", len(df), "| event_rate", round(df.event.mean(), 3),
          "| K", K, "| train", int((df.split == "train").sum()), "test", int((df.split == "test").sum()))
    print("events by stage:\n", df.groupby("stage").event.mean().round(3))
    print("event rate by treatment:\n", df.groupby("treatment").event.mean().round(3))
    print("time_observed dist:\n", df.time_observed.value_counts().sort_index().to_dict())
