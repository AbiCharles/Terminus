#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: build the `features` table in /app/fraud.duckdb from the
# raw `transactions` table using SQL window functions, per the §2 feature
# definitions in /app/spec.md.
cat > /app/build_features.py <<'PY'
"""Create the features table via DuckDB SQL window functions."""
import duckdb

con = duckdb.connect("/app/fraud.duckdb")
con.execute("DROP TABLE IF EXISTS features")
con.execute(
    """
    CREATE TABLE features AS
    SELECT
        transaction_id, account_id, ts, is_fraud, split,
        COALESCE(epoch(ts) - epoch(lag(ts) OVER w), 0)        AS prev_txn_gap_sec,
        (row_number() OVER w) - 1                              AS acct_txn_index,
        COUNT(*) OVER w1h                                      AS amt_count_1h,
        SUM(amount) OVER w24h                                  AS amt_sum_24h,
        COALESCE(AVG(amount) OVER wprev5, 0)                   AS amt_avg_prev5,
        CASE WHEN COALESCE(AVG(amount) OVER wprev5, 0) = 0 THEN 0
             ELSE amount / AVG(amount) OVER wprev5 END         AS amt_ratio_prev5
    FROM transactions
    WINDOW
        w      AS (PARTITION BY account_id ORDER BY ts),
        w1h    AS (PARTITION BY account_id ORDER BY ts
                   RANGE BETWEEN INTERVAL 1 HOUR PRECEDING AND CURRENT ROW),
        w24h   AS (PARTITION BY account_id ORDER BY ts
                   RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW),
        wprev5 AS (PARTITION BY account_id ORDER BY ts
                   ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING)
    """
)
n = con.execute("SELECT COUNT(*) FROM features").fetchone()[0]
con.close()
print(f"features table built: {n} rows")
PY

python3 /app/build_features.py
