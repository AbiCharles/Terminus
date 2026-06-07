"""Reference competing-risks + time-varying survival pipeline (dev tuning)."""

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

K = 12
FEATURES = ["age", "log_biomarker", "treatment", "stage_II", "stage_III", "sex_M", "period"]

# person-period with LOCF biomarker via ASOF JOIN + 3-class period outcome
PP_SQL = """
WITH skeleton AS (
    SELECT s.subject_id, CAST(p.period AS INTEGER) AS period,
           s.age, s.treatment, s.stage, s.sex, s.split, s.time_observed, s.event_type
    FROM subjects s, generate_series(1, s.time_observed) AS p(period)
)
SELECT k.subject_id, k.period, k.age, m.biomarker, k.treatment, k.stage, k.sex,
       k.split, k.time_observed, k.event_type,
       CASE WHEN k.event_type = 1 AND k.period = k.time_observed THEN 1
            WHEN k.event_type = 2 AND k.period = k.time_observed THEN 2
            ELSE 0 END AS period_outcome
FROM skeleton k
ASOF LEFT JOIN measurements m
  ON m.subject_id = k.subject_id AND m.period <= k.period
ORDER BY k.subject_id, k.period
"""


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


def cif_curves(model, subjects, measurements):
    """Return per-subject DataFrame with period, h1, h2, surv, cif1, cif2."""
    grid = subjects.loc[subjects.index.repeat(K)].copy()
    grid["period"] = np.tile(np.arange(1, K + 1), len(subjects))
    # LOCF biomarker for each (subject, period) via merge_asof (on-key sorted globally)
    meas = measurements.sort_values("period")
    grid = grid.sort_values("period")
    grid = pd.merge_asof(grid, meas, on="period", by="subject_id", direction="backward")
    proba = model.predict_proba(design(grid))
    cls = list(model.classes_)
    grid["h1"] = proba[:, cls.index(1)]
    grid["h2"] = proba[:, cls.index(2)]
    out = []
    for _, g in grid.groupby("subject_id", sort=False):
        g = g.sort_values("period")
        h1, h2 = g["h1"].to_numpy(), g["h2"].to_numpy()
        surv_prev = np.concatenate([[1.0], np.cumprod(1.0 - h1 - h2)[:-1]])
        cif1 = np.cumsum(h1 * surv_prev)
        cif2 = np.cumsum(h2 * surv_prev)
        g = g.assign(surv=np.cumprod(1.0 - h1 - h2), cif1=cif1, cif2=cif2)
        out.append(g[["subject_id", "period", "cif1", "cif2", "surv"]])
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
    cens = (np.asarray(etype) == 0)
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


def main():
    con = duckdb.connect("survival_cr.duckdb")
    pp = con.execute(PP_SQL).df()
    subjects = con.execute("SELECT * FROM subjects").df()
    measurements = con.execute("SELECT * FROM measurements").df()
    con.close()

    train = pp[pp["split"] == "train"]
    model = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs", random_state=42)
    model.fit(design(train), train["period_outcome"].to_numpy(int))

    test = subjects[subjects["split"] == "test"].reset_index(drop=True)
    curves = cif_curves(model, test, measurements)
    risk1 = curves[curves["period"] == K].set_index("subject_id")["cif1"]
    merged = test.set_index("subject_id").join(risk1.rename("risk1"))
    c = c_index_cause1(merged["time_observed"], merged["event_type"], merged["risk1"])
    ibs = integrated_brier_cause1(curves, test)
    print(f"pp rows {len(pp)} | classes {list(model.classes_)} | null biomarker {pp.biomarker.isna().sum()}")
    print(f"cause1 C-index: {c:.4f}")
    print(f"cause1 IPCW IBS: {ibs:.4f}")
    print(f"coef cause1: {dict(zip(FEATURES, model.coef_[list(model.classes_).index(1)].round(3)))}")


if __name__ == "__main__":
    main()
