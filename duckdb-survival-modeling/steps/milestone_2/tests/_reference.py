"""Independent reference implementation of the survival pipeline.

Recomputes, from the raw `subjects` table in /app/survival.duckdb alone, the exact
person-period expansion, the discrete-time hazard model, the per-test-subject
survival curves and risk scores, and the C-index / IPCW Integrated Brier Score
(mirroring /app/spec.md). It does NOT trust the agent's derived tables — it is the
verifier's answer key. The agent has no access to this module at solve time.
"""

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

DB_PATH = "/app/survival.duckdb"
K = 12
FEATURES = ["age", "log_biomarker", "treatment", "stage_II", "stage_III", "sex_M", "period"]


def load_subjects():
    con = duckdb.connect(DB_PATH, read_only=True)
    subjects = con.execute("SELECT * FROM subjects").df()
    con.close()
    return subjects


def expected_person_period(subjects):
    rows = subjects.loc[subjects.index.repeat(subjects["time_observed"].to_numpy())].copy()
    rows["period"] = np.concatenate([np.arange(1, n + 1) for n in subjects["time_observed"]])
    rows["event_in_period"] = (
        (rows["event"] == 1) & (rows["period"] == rows["time_observed"])
    ).astype(int)
    return rows[["subject_id", "period", "age", "biomarker", "treatment",
                 "stage", "sex", "split", "event_in_period"]].reset_index(drop=True)


def design(df):
    return pd.DataFrame({
        "age": df["age"].to_numpy(float),
        "log_biomarker": np.log(df["biomarker"].to_numpy(float)),
        "treatment": df["treatment"].to_numpy(float),
        "stage_II": (df["stage"] == "II").astype(float),
        "stage_III": (df["stage"] == "III").astype(float),
        "sex_M": (df["sex"] == "M").astype(float),
        "period": df["period"].to_numpy(float),
    })[FEATURES]


def reference_model(subjects=None):
    if subjects is None:
        subjects = load_subjects()
    pp = expected_person_period(subjects)
    train = pp[pp["split"] == "train"]
    model = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs", random_state=42)
    model.fit(design(train), train["event_in_period"].to_numpy(int))
    return model


def survival_curves(model, subjects):
    rows = subjects.loc[subjects.index.repeat(K)].copy()
    rows["period"] = np.tile(np.arange(1, K + 1), len(subjects))
    rows["hazard"] = model.predict_proba(design(rows))[:, 1]
    rows["survival_prob"] = rows.groupby("subject_id")["hazard"].transform(
        lambda h: np.cumprod(1.0 - h.to_numpy())
    )
    return rows[["subject_id", "period", "survival_prob"]].reset_index(drop=True)


def harrell_c_index(time, event, risk):
    time, event, risk = np.asarray(time), np.asarray(event), np.asarray(risk)
    conc = tied = comp = 0.0
    for i in range(len(time)):
        if event[i] != 1:
            continue
        later = time > time[i]
        comp += later.sum()
        conc += np.sum(risk[i] > risk[later])
        tied += np.sum(risk[i] == risk[later])
    return (conc + 0.5 * tied) / comp if comp else float("nan")


def km_censoring(time, event):
    time, event = np.asarray(time), np.asarray(event)
    g, prev, at_risk = {}, 1.0, len(time)
    for u in np.unique(time):
        c_u = int(np.sum((time == u) & (event == 0)))
        d_u = int(np.sum(time == u))
        prev = prev * (1.0 - c_u / at_risk) if at_risk > 0 else prev
        g[u] = prev
        at_risk -= d_u
    return g


def g_at(g, query):
    val = 1.0
    for k in sorted(g):
        if k <= query:
            val = g[k]
        else:
            break
    return val


def integrated_brier(curves, subjects):
    piv = curves.pivot(index="subject_id", columns="period", values="survival_prob")
    meta = subjects.set_index("subject_id").loc[piv.index]
    t, e = meta["time_observed"].to_numpy(), meta["event"].to_numpy()
    g = km_censoring(t, e)
    n = len(piv)
    bs = []
    for horizon in range(1, K + 1):
        s_t = piv[horizon].to_numpy()
        total = 0.0
        for i in range(n):
            if t[i] <= horizon and e[i] == 1:
                gw = g_at(g, t[i])
                if gw > 0:
                    total += s_t[i] ** 2 / gw
            elif t[i] > horizon:
                gw = g_at(g, horizon)
                if gw > 0:
                    total += (1.0 - s_t[i]) ** 2 / gw
        bs.append(total / n)
    return float(np.mean(bs))


def reference_outputs():
    """Return reference test-set curves, risk scores, and metrics from scratch."""
    subjects = load_subjects()
    model = reference_model(subjects)
    test = subjects[subjects["split"] == "test"].reset_index(drop=True)
    curves = survival_curves(model, test)
    risk = (1.0 - curves[curves["period"] == K].set_index("subject_id")["survival_prob"])
    risk = risk.rename("risk_score").reset_index()
    merged = test.merge(risk, on="subject_id")
    c_index = harrell_c_index(merged["time_observed"], merged["event"], merged["risk_score"])
    ibs = integrated_brier(curves, test)
    return {"model": model, "test": test, "curves": curves, "risk": merged,
            "c_index": c_index, "integrated_brier_score": ibs}
