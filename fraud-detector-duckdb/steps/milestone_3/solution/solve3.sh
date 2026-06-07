#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: write the /app/score.py batch-scoring CLI and run it. It
# loads the saved model, scores the score-split features, and writes the
# scored_transactions table per §4 of /app/spec.md.
cat > /app/score.py <<'PY'
"""Batch fraud-scoring CLI: write scored_transactions from the saved model."""
import argparse

import duckdb
import joblib
import pandas as pd

FEATURES = [
    "prev_txn_gap_sec",
    "acct_txn_index",
    "amt_count_1h",
    "amt_sum_24h",
    "amt_avg_prev5",
    "amt_ratio_prev5",
]


def main():
    parser = argparse.ArgumentParser(description="Score score-split transactions for fraud.")
    parser.add_argument("--db", default="/app/fraud.duckdb", help="DuckDB database path")
    parser.add_argument("--model", default="/app/artifacts/fraud_model.joblib", help="model artifact path")
    args = parser.parse_args()

    model = joblib.load(args.model)
    con = duckdb.connect(args.db)
    rows = con.execute(
        "SELECT * FROM features WHERE split = 'score' ORDER BY transaction_id"
    ).df()
    proba = model.predict_proba(rows[FEATURES])[:, 1]
    out = pd.DataFrame(
        {
            "transaction_id": rows["transaction_id"].to_numpy(),
            "fraud_probability": proba,
            "fraud_prediction": (proba >= 0.5).astype("int32"),
        }
    )
    con.execute("DROP TABLE IF EXISTS scored_transactions")
    con.execute(
        "CREATE TABLE scored_transactions "
        "(transaction_id BIGINT, fraud_probability DOUBLE, fraud_prediction INTEGER)"
    )
    con.execute("INSERT INTO scored_transactions SELECT * FROM out")
    n = con.execute("SELECT COUNT(*) FROM scored_transactions").fetchone()[0]
    con.close()
    print(f"scored_transactions written: {n} rows")


if __name__ == "__main__":
    main()
PY

python3 /app/score.py
