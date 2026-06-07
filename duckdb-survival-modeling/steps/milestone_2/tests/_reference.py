"""Independent reference for the competing-risks + time-varying survival pipeline.

Recomputes, from the raw `subjects` and `measurements` tables alone, the LOCF
person-period expansion, the multinomial discrete-time hazard model, the CIF
curves, and the cause-1 C-index / competing-risks IPCW Integrated Brier Score
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


def load_tables():
    con = duckdb.connect(DB_PATH, read_only=True)
    subjects = con.execute("SELECT * FROM subjects").df()
    measurements = con.execute("SELECT * FROM measurements").df()
    con.close()
    return subjects, measurements


def _locf_grid(subjects, measurements, period_upper):
    """subjects x periods 1..period_upper(row) with LOCF biomarker attached."""
    counts = period_upper.to_numpy()
    grid = subjects.loc[subjects.index.repeat(counts)].copy()
    grid["period"] = np.concatenate([np.arange(1, n + 1) for n in counts])
    grid = grid.sort_values("period")
    meas = measurements.sort_values("period")
    grid = pd.merge_asof(grid, meas, on="period", by="subject_id", direction="backward")
    return grid


def expected_person_period(subjects, measurements):
    grid = _locf_grid(subjects, measurements, subjects["time_observed"])
    grid["period_outcome"] = np.select(
        [(grid["event_type"] == 1) & (grid["period"] == grid["time_observed"]),
         (grid["event_type"] == 2) & (grid["period"] == grid["time_observed"])],
        [1, 2], default=0,
    ).astype(int)
    return grid[["subject_id", "period", "age", "biomarker", "treatment",
                 "stage", "sex", "split", "period_outcome"]].reset_index(drop=True)


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


def reference_model(subjects=None, measurements=None):
    if subjects is None:
        subjects, measurements = load_tables()
    pp = expected_person_period(subjects, measurements)
    train = pp[pp["split"] == "train"]
    model = LogisticRegression(C=1.0, max_iter=5000, solver="lbfgs", tol=1e-8, random_state=42)
    model.fit(design(train), train["period_outcome"].to_numpy(int))
    return model


def cif_curves(model, subjects, measurements):
    full_k = pd.Series(np.full(len(subjects), K), index=subjects.index)
    grid = _locf_grid(subjects.reset_index(drop=True), measurements, full_k)
    proba = model.predict_proba(design(grid))
    cls = list(model.classes_)
    grid["h1"] = proba[:, cls.index(1)]
    grid["h2"] = proba[:, cls.index(2)]
    out = []
    for _, g in grid.groupby("subject_id", sort=False):
        g = g.sort_values("period")
        h1, h2 = g["h1"].to_numpy(), g["h2"].to_numpy()
        surv = np.cumprod(1.0 - h1 - h2)
        surv_prev = np.concatenate([[1.0], surv[:-1]])
        out.append(g.assign(
            survival_prob=surv,
            cif1=np.cumsum(h1 * surv_prev),
            cif2=np.cumsum(h2 * surv_prev),
        )[["subject_id", "period", "cif1", "cif2", "survival_prob"]])
    return pd.concat(out, ignore_index=True)


def c_index_cause1(time, etype, risk):
    time, etype, risk = np.asarray(time), np.asarray(etype), np.asarray(risk)
    conc = tied = comp = 0.0
    for i in range(len(time)):
        if etype[i] != 1:
            continue
        later = time > time[i]
        comp += later.sum()
        conc += np.sum(risk[i] > risk[later])
        tied += np.sum(risk[i] == risk[later])
    return (conc + 0.5 * tied) / comp if comp else float("nan")


def km_censoring(time, etype):
    time = np.asarray(time)
    cens = np.asarray(etype) == 0
    g, prev, at_risk = {}, 1.0, len(time)
    for u in np.unique(time):
        c_u = int(np.sum((time == u) & cens))
        d_u = int(np.sum(time == u))
        prev = prev * (1.0 - c_u / at_risk) if at_risk > 0 else prev
        g[u] = prev
        at_risk -= d_u
    return g


def g_at(g, q):
    val = 1.0
    for k in sorted(g):
        if k <= q:
            val = g[k]
        else:
            break
    return val


def integrated_brier_cause1(curves, subjects):
    piv = curves.pivot(index="subject_id", columns="period", values="cif1")
    meta = subjects.set_index("subject_id").loc[piv.index]
    t, e = meta["time_observed"].to_numpy(), meta["event_type"].to_numpy()
    g = km_censoring(t, e)
    n = len(piv)
    bs = []
    for horizon in range(1, K + 1):
        cif = piv[horizon].to_numpy()
        total = 0.0
        for i in range(n):
            if t[i] <= horizon and e[i] == 1:
                gw = g_at(g, t[i])
                if gw > 0:
                    total += (cif[i] - 1.0) ** 2 / gw
            elif t[i] <= horizon and e[i] == 2:
                gw = g_at(g, t[i])
                if gw > 0:
                    total += cif[i] ** 2 / gw
            elif t[i] > horizon:
                gw = g_at(g, horizon)
                if gw > 0:
                    total += cif[i] ** 2 / gw
        bs.append(total / n)
    return float(np.mean(bs))


def reference_outputs():
    subjects, measurements = load_tables()
    model = reference_model(subjects, measurements)
    test = subjects[subjects["split"] == "test"].reset_index(drop=True)
    curves = cif_curves(model, test, measurements)
    risk = curves[curves["period"] == K].set_index("subject_id")["cif1"].rename("risk_score").reset_index()
    merged = test.merge(risk, on="subject_id")
    c_index = c_index_cause1(merged["time_observed"], merged["event_type"], merged["risk_score"])
    ibs = integrated_brier_cause1(curves, test)
    return {"model": model, "test": test, "measurements": measurements, "curves": curves,
            "risk": merged, "c_index": c_index, "integrated_brier_score": ibs}
