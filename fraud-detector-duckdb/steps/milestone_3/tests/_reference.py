"""Independent reference computations for the fraud-detector verifier.

Recomputes the feature frames in pandas directly from the raw `transactions`
table (a re-implementation of the spec's window definitions) and provides the
reference model + metrics. The verifier never trusts the agent's tables for
correctness — it recomputes ground truth here. Not available to the agent at
solve time.
"""
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

DB_PATH = "/app/fraud.duckdb"
ARTIFACT_PATH = "/app/artifacts/fraud_model.joblib"
FEATURES = [
    "prev_txn_gap_sec",
    "acct_txn_index",
    "amt_count_1h",
    "amt_sum_24h",
    "amt_avg_prev5",
    "amt_ratio_prev5",
]

# Integrity constants for the shipped `transactions` table (anti-tamper).
TXN_COUNT = 40186
AMOUNT_SUM = 2501512.38
FRAUD_SUM = 2115
SCORE_COUNT = 12405
TRAIN_COUNT = 27781


def connect(read_only=True):
    return duckdb.connect(DB_PATH, read_only=read_only)


def compute_reference_features(con):
    """Recompute the six features per spec, from the raw transactions table."""
    df = con.execute(
        "SELECT transaction_id, account_id, epoch(ts) AS te, amount, is_fraud, split "
        "FROM transactions ORDER BY account_id, ts, transaction_id"
    ).df()
    out = []
    for _, g in df.groupby("account_id", sort=False):
        te = g["te"].to_numpy()
        amt = g["amount"].to_numpy()
        n = len(g)
        gap = np.zeros(n)
        gap[1:] = te[1:] - te[:-1]
        idx = np.arange(n, dtype=float)
        cnt1h = np.empty(n)
        sum24 = np.empty(n)
        csum = np.concatenate([[0.0], np.cumsum(amt)])
        for i in range(n):
            lo1 = np.searchsorted(te, te[i] - 3600, side="left")
            cnt1h[i] = i - lo1 + 1
            lo24 = np.searchsorted(te, te[i] - 86400, side="left")
            sum24[i] = csum[i + 1] - csum[lo24]
        avg5 = np.zeros(n)
        for i in range(1, n):
            lo = max(0, i - 5)
            avg5[i] = amt[lo:i].mean()
        ratio = np.where(avg5 == 0, 0.0, amt / np.where(avg5 == 0, 1.0, avg5))
        r = g[["transaction_id", "is_fraud", "split"]].copy()
        r["prev_txn_gap_sec"] = gap
        r["acct_txn_index"] = idx
        r["amt_count_1h"] = cnt1h
        r["amt_sum_24h"] = sum24
        r["amt_avg_prev5"] = avg5
        r["amt_ratio_prev5"] = ratio
        out.append(r)
    return pd.concat(out).sort_values("transaction_id").reset_index(drop=True)


def reference_model(features_df):
    """Fit the spec GradientBoostingClassifier on the train-split features."""
    train = features_df[features_df["split"] == "train"]
    clf = GradientBoostingClassifier(
        n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42
    )
    clf.fit(train[FEATURES], train["is_fraud"])
    return clf


def reference_metrics(features_df, model=None):
    """Score-split metrics for the reference model trained on features_df."""
    if model is None:
        model = reference_model(features_df)
    score = features_df[features_df["split"] == "score"]
    proba = model.predict_proba(score[FEATURES])[:, 1]
    pred = (proba >= 0.5).astype(int)
    y = score["is_fraud"]
    return {
        "roc_auc": float(roc_auc_score(y, proba)),
        "average_precision": float(average_precision_score(y, proba)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
    }
