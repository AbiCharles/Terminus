"""Competing-risks + time-varying clinical survival fixture.

Two event types compete (cause 1 = disease progression, cause 2 = other-cause),
plus right-censoring. A time-varying biomarker is measured at sparse visit periods
and is constant between visits (step function), so the discrete hazards in each
period depend on the biomarker value carried forward from the most recent visit.
This forces a correct LOCF temporal join when building person-period rows.

Tables written to survival_cr.duckdb:
  subjects(subject_id, age, treatment, stage, sex, time_observed, event_type, split)
  measurements(subject_id, period, biomarker)        -- longitudinal, sparse
"""

import numpy as np
import pandas as pd
import duckdb

RNG = np.random.default_rng(20240307)
N = 3000
K = 12

# baseline per-period hazard offsets for the two causes
g1 = np.linspace(-3.4, -2.6, K)   # cause 1 (disease) rises over time
g2 = np.full(K, -3.6)             # cause 2 (other-cause) roughly flat


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


age = np.clip(RNG.normal(61, 11, N), 30, 90).round(1)
treatment = RNG.integers(0, 2, N)
stage = RNG.choice(["I", "II", "III"], size=N, p=[0.4, 0.38, 0.22])
sex = RNG.choice(["F", "M"], size=N, p=[0.5, 0.5])
age_z = (age - 61) / 11
stage_eff = np.select([stage == "I", stage == "II", stage == "III"], [0.0, 0.5, 1.1])

# each subject's biomarker trajectory: visits at sparse periods, step-constant.
# higher long-run biomarker -> higher cause-1 hazard. Visit grid starts at 1.
base_log_bio = RNG.normal(1.0, 0.5, N)          # baseline log-biomarker
drift = RNG.normal(0.06, 0.04, N)               # per-period upward drift

subj_rows = []
meas_rows = []
for i in range(N):
    # visit periods: 1, then every 2-3 periods
    visits = [1]
    p = 1
    while p < K:
        p += int(RNG.integers(2, 4))
        if p <= K:
            visits.append(p)
    visit_bio = {}
    for v in visits:
        val = float(np.exp(base_log_bio[i] + drift[i] * (v - 1) + RNG.normal(0, 0.12)))
        visit_bio[v] = round(np.clip(val, 0.2, 40.0), 3)

    def locf_bio(t, visits=visits, visit_bio=visit_bio):
        last = max(v for v in visits if v <= t)
        return visit_bio[last]

    # simulate competing-risks event sequentially using the period's LOCF biomarker
    event_t, event_type = K + 1, 0
    for t in range(1, K + 1):
        lb = np.log(locf_bio(t))
        h1 = sigmoid(g1[t - 1] + 0.55 * age_z[i] + 0.9 * (lb - 1.0) - 0.8 * treatment[i] + stage_eff[i])
        h2 = sigmoid(g2[t - 1] + 0.8 * age_z[i] + 0.1 * (lb - 1.0))
        u = RNG.random()
        if u < h1:
            event_t, event_type = t, 1
            break
        if u < h1 + h2:
            event_t, event_type = t, 2
            break
    # random dropout + administrative censoring at K
    drop_t = K + 1
    for t in range(1, K + 1):
        if RNG.random() < 0.025:
            drop_t = t
            break
    censor_t = min(drop_t, K)
    if event_t <= censor_t:
        time_observed, etype = event_t, event_type
    else:
        time_observed, etype = censor_t, 0

    subj_rows.append((i + 1, age[i], treatment[i], stage[i], sex[i], time_observed, etype))
    for v in visits:
        if v <= time_observed:
            meas_rows.append((i + 1, v, visit_bio[v]))

split = np.where(RNG.random(N) < 0.70, "train", "test")
subjects = pd.DataFrame(subj_rows, columns=["subject_id", "age", "treatment", "stage", "sex", "time_observed", "event_type"])
subjects["split"] = split
measurements = pd.DataFrame(meas_rows, columns=["subject_id", "period", "biomarker"])

if __name__ == "__main__":
    con = duckdb.connect("survival_cr.duckdb")
    con.execute("DROP TABLE IF EXISTS subjects; DROP TABLE IF EXISTS measurements")
    con.execute("CREATE TABLE subjects AS SELECT * FROM subjects")
    con.execute("CREATE TABLE measurements AS SELECT * FROM measurements")
    con.close()
    print("subjects", len(subjects), "| measurements", len(measurements))
    print("event_type dist:", subjects.event_type.value_counts().sort_index().to_dict())
    print("cause1 by stage:\n", subjects.assign(c1=(subjects.event_type == 1).astype(int)).groupby("stage").c1.mean().round(3))
    print("cause1 by treatment:", subjects.assign(c1=(subjects.event_type == 1).astype(int)).groupby("treatment").c1.mean().round(3).to_dict())
    print("avg measurements/subject:", round(len(measurements) / len(subjects), 2))
