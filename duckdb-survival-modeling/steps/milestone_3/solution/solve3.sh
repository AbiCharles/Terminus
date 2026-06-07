#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: write the scoring CLI and run it. It reloads the serialized
# model, computes per-test-subject survival curves and risk scores, evaluates the
# censoring-aware C-index and IPCW Integrated Brier Score (per /app/spec.md §5),
# and writes survival_curves / risk_scores / model_metrics tables plus
# /app/artifacts/predictions.csv.
cat > /app/score.py <<'PY'
"""Score test subjects: survival curves, risk scores, C-index and IPCW IBS."""
import duckdb
import joblib
import numpy as np
import pandas as pd

K = 12
FEATURES = ["age", "log_biomarker", "treatment", "stage_II", "stage_III", "sex_M", "period"]


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


def main():
    model = joblib.load("/app/artifacts/survival_model.joblib")
    con = duckdb.connect("/app/survival.duckdb")
    test = con.execute("SELECT * FROM subjects WHERE split = 'test'").df().reset_index(drop=True)

    curves = survival_curves(model, test)
    risk = (1.0 - curves[curves["period"] == K].set_index("subject_id")["survival_prob"]).rename("risk_score")
    risk_df = risk.reset_index()
    merged = test.merge(risk_df, on="subject_id")

    c_index = harrell_c_index(merged["time_observed"], merged["event"], merged["risk_score"])
    ibs = integrated_brier(curves, test)

    preds = merged[["subject_id", "risk_score"]].copy()
    preds["survival_prob_at_K"] = 1.0 - preds["risk_score"]
    import os
    os.makedirs("/app/artifacts", exist_ok=True)
    preds.to_csv("/app/artifacts/predictions.csv", index=False)

    metrics = pd.DataFrame({"metric": ["c_index", "integrated_brier_score"], "value": [c_index, ibs]})
    con.execute("DROP TABLE IF EXISTS survival_curves")
    con.execute("CREATE TABLE survival_curves AS SELECT * FROM curves")
    con.execute("DROP TABLE IF EXISTS risk_scores")
    con.execute("CREATE TABLE risk_scores AS SELECT * FROM risk_df")
    con.execute("DROP TABLE IF EXISTS model_metrics")
    con.execute("CREATE TABLE model_metrics AS SELECT * FROM metrics")
    con.close()
    print(f"c_index={c_index:.4f} integrated_brier_score={ibs:.4f}")


if __name__ == "__main__":
    main()
PY

python3 /app/score.py
