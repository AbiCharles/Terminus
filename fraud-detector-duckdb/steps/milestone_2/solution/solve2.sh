#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: train the GradientBoostingClassifier on the train-split
# features, persist it with joblib, and write the score-split evaluation metrics
# to the model_metrics table, per §3 of /app/spec.md.
cat > /app/train_model.py <<'PY'
"""Train the fraud classifier, save the artifact, and write model_metrics."""
import os

import duckdb
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

FEATURES = [
    "prev_txn_gap_sec",
    "acct_txn_index",
    "amt_count_1h",
    "amt_sum_24h",
    "amt_avg_prev5",
    "amt_ratio_prev5",
]

con = duckdb.connect("/app/fraud.duckdb")
df = con.execute("SELECT * FROM features").df()
train = df[df["split"] == "train"]
score = df[df["split"] == "score"]

clf = GradientBoostingClassifier(
    n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42
)
clf.fit(train[FEATURES], train["is_fraud"])

os.makedirs("/app/artifacts", exist_ok=True)
joblib.dump(clf, "/app/artifacts/fraud_model.joblib")

proba = clf.predict_proba(score[FEATURES])[:, 1]
pred = (proba >= 0.5).astype(int)
y = score["is_fraud"]
metrics = {
    "roc_auc": float(roc_auc_score(y, proba)),
    "average_precision": float(average_precision_score(y, proba)),
    "precision": float(precision_score(y, pred, zero_division=0)),
    "recall": float(recall_score(y, pred, zero_division=0)),
    "f1": float(f1_score(y, pred, zero_division=0)),
}

con.execute("DROP TABLE IF EXISTS model_metrics")
con.execute("CREATE TABLE model_metrics (metric VARCHAR, value DOUBLE)")
con.executemany("INSERT INTO model_metrics VALUES (?, ?)", list(metrics.items()))
con.close()
print("trained model + metrics:", {k: round(v, 4) for k, v in metrics.items()})
PY

python3 /app/train_model.py
