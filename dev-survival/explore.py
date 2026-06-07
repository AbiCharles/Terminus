"""Reference discrete-time survival pipeline — used in dev to tune signal and to
pin the exact, deterministic definitions the spec/oracle/verifier will share.

Pipeline:
  1. person-period expansion via DuckDB SQL (correlated generate_series)
  2. discrete-time logistic-regression hazard model (sklearn)
  3. per-subject survival curve S(t)=prod(1-h(k)) and risk = 1-S(K)
  4. Harrell C-index (censoring-aware) and IPCW Integrated Brier Score
"""

import duckdb
import joblib  # noqa: F401  (used by oracle/tests; imported to confirm availability)
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

K = 12
HORIZON = K
FEATURES = ["age", "log_biomarker", "treatment", "stage_II", "stage_III", "sex_M", "period"]

PERSON_PERIOD_SQL = """
SELECT s.subject_id, p.period,
       s.age, s.biomarker, s.treatment, s.stage, s.sex, s.time_observed, s.event, s.split,
       CASE WHEN s.event = 1 AND p.period = s.time_observed THEN 1 ELSE 0 END AS event_in_period
FROM subjects s, generate_series(1, s.time_observed) AS p(period)
ORDER BY s.subject_id, p.period
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


def survival_curves(model, subjects):
    """Return DataFrame [subject_id, period, surv] over period 1..K for given subjects."""
    rows = subjects.loc[subjects.index.repeat(K)].copy()
    rows["period"] = np.tile(np.arange(1, K + 1), len(subjects))
    haz = model.predict_proba(design(rows))[:, 1]
    rows = rows.assign(hazard=haz)
    rows["surv"] = rows.groupby("subject_id")["hazard"].transform(lambda h: np.cumprod(1.0 - h.to_numpy()))
    return rows[["subject_id", "period", "surv"]]


def harrell_c_index(time, event, risk):
    """Censoring-aware concordance: comparable pair (i,j) iff the earlier time is an event."""
    time, event, risk = map(np.asarray, (time, event, risk))
    n = len(time)
    conc = tied = comp = 0.0
    for i in range(n):
        if event[i] != 1:
            continue
        mask = time > time[i]
        comp += mask.sum()
        conc += np.sum(risk[i] > risk[mask])
        tied += np.sum(risk[i] == risk[mask])
    return (conc + 0.5 * tied) / comp if comp else float("nan")


def km_censoring(time, event):
    """KM estimate G(t) of the censoring-survival function (censoring treated as event)."""
    order = np.argsort(time, kind="mergesort")
    t, e = np.asarray(time)[order], np.asarray(event)[order]
    uniq = np.unique(t)
    g, prev, n = {}, 1.0, len(t)
    at_risk = n
    for ut in uniq:
        d_cens = np.sum((t == ut) & (e == 0))
        d_any = np.sum(t == ut)
        prev = prev * (1.0 - d_cens / at_risk) if at_risk > 0 else prev
        g[ut] = prev
        at_risk -= d_any
    return g


def g_at(g, query):
    """Left-continuous lookup: largest event-time <= query (1.0 before the first)."""
    keys = sorted(g)
    val = 1.0
    for k in keys:
        if k <= query:
            val = g[k]
        else:
            break
    return val


def brier_at(t_star, time, event, surv_t):
    """IPCW Brier score at horizon t_star. surv_t = predicted S(t_star) per subject."""
    g = km_censoring(time, event)
    total = 0.0
    for i in range(len(time)):
        ti, ei, si = time[i], event[i], surv_t[i]
        if ti <= t_star and ei == 1:
            gw = g_at(g, ti)
            if gw > 0:
                total += (si ** 2) / gw
        elif ti > t_star:
            gw = g_at(g, t_star)
            if gw > 0:
                total += ((1.0 - si) ** 2) / gw
        # censored before t_star -> weight 0 (excluded)
    return total / len(time)


def integrated_brier(curves, subjects):
    time = subjects.set_index("subject_id").loc[curves["subject_id"].unique(), "time_observed"]
    piv = curves.pivot(index="subject_id", columns="period", values="surv")
    t = subjects.set_index("subject_id").loc[piv.index, "time_observed"].to_numpy()
    e = subjects.set_index("subject_id").loc[piv.index, "event"].to_numpy()
    bs = [brier_at(ts, t, e, piv[ts].to_numpy()) for ts in range(1, K + 1)]
    return float(np.mean(bs)), bs


def main():
    con = duckdb.connect("survival.duckdb")
    pp = con.execute(PERSON_PERIOD_SQL).df()
    subjects = con.execute("SELECT * FROM subjects").df()
    con.close()

    train = pp[pp["split"] == "train"]
    model = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs", random_state=42)
    model.fit(design(train), train["event_in_period"].to_numpy())

    test_subj = subjects[subjects["split"] == "test"].reset_index(drop=True)
    curves = survival_curves(model, test_subj)
    risk = 1.0 - curves[curves["period"] == HORIZON].set_index("subject_id")["surv"]
    risk = test_subj.set_index("subject_id").join(risk.rename("risk"))

    c = harrell_c_index(risk["time_observed"], risk["event"], risk["risk"])
    ibs, bs = integrated_brier(curves, test_subj)
    print(f"person_period rows: {len(pp)} (train {len(train)})")
    print(f"C-index (test): {c:.4f}")
    print(f"Integrated Brier Score (test): {ibs:.4f}")
    print(f"Brier by horizon: {[round(b,4) for b in bs]}")
    print(f"model coefs: {dict(zip(FEATURES, model.coef_[0].round(4)))}")


if __name__ == "__main__":
    main()
