"""Build features via DuckDB windows, verify pandas parity, train, report metrics."""
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

FEATURES = [
    "prev_txn_gap_sec",
    "acct_txn_index",
    "amt_count_1h",
    "amt_sum_24h",
    "amt_avg_prev5",
    "amt_ratio_prev5",
]

FEATURE_SQL = """
SELECT
    transaction_id, account_id, ts, is_fraud, split,
    COALESCE(epoch(ts) - epoch(lag(ts) OVER w), 0)            AS prev_txn_gap_sec,
    (row_number() OVER w) - 1                                  AS acct_txn_index,
    COUNT(*) OVER w1h                                          AS amt_count_1h,
    SUM(amount) OVER w24h                                      AS amt_sum_24h,
    COALESCE(AVG(amount) OVER wprev5, 0)                       AS amt_avg_prev5,
    CASE WHEN COALESCE(AVG(amount) OVER wprev5, 0) = 0 THEN 0
         ELSE amount / AVG(amount) OVER wprev5 END             AS amt_ratio_prev5
FROM transactions
WINDOW
    w     AS (PARTITION BY account_id ORDER BY ts),
    w1h   AS (PARTITION BY account_id ORDER BY ts RANGE BETWEEN INTERVAL 1 HOUR PRECEDING AND CURRENT ROW),
    w24h  AS (PARTITION BY account_id ORDER BY ts RANGE BETWEEN INTERVAL 24 HOUR PRECEDING AND CURRENT ROW),
    wprev5 AS (PARTITION BY account_id ORDER BY ts ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING)
ORDER BY transaction_id
"""


def pandas_reference(con):
    """Recompute the exact feature frames in pandas from the raw transactions."""
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
        for i in range(n):
            if i == 0:
                avg5[i] = 0.0
            else:
                lo = max(0, i - 5)
                avg5[i] = amt[lo:i].mean()
        ratio = np.where(avg5 == 0, 0.0, amt / np.where(avg5 == 0, 1, avg5))
        r = g[["transaction_id"]].copy()
        r["prev_txn_gap_sec"] = gap
        r["acct_txn_index"] = idx
        r["amt_count_1h"] = cnt1h
        r["amt_sum_24h"] = sum24
        r["amt_avg_prev5"] = avg5
        r["amt_ratio_prev5"] = ratio
        out.append(r)
    return pd.concat(out).sort_values("transaction_id").reset_index(drop=True)


def main():
    con = duckdb.connect("fraud.duckdb", read_only=True)
    feats = con.execute(FEATURE_SQL).df()
    ref = pandas_reference(con)

    # ---- parity check: DuckDB SQL vs pandas recompute ----
    merged = feats.sort_values("transaction_id").reset_index(drop=True)
    print("=== DuckDB vs pandas parity (max abs diff per feature) ===")
    worst = 0.0
    for col in FEATURES:
        d = np.abs(merged[col].to_numpy(float) - ref[col].to_numpy(float)).max()
        worst = max(worst, d)
        print(f"  {col:18s} maxdiff={d:.3e}")
    print(f"  WORST={worst:.3e}", "OK" if worst < 1e-9 else "MISMATCH!")

    # ---- train + evaluate ----
    train = merged[merged.split == "train"]
    score = merged[merged.split == "score"]
    clf = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42)
    clf.fit(train[FEATURES], train["is_fraud"])
    proba = clf.predict_proba(score[FEATURES])[:, 1]
    pred = (proba >= 0.5).astype(int)
    y = score["is_fraud"].to_numpy()
    print("\n=== model metrics on score split ===")
    print(f"  roc_auc          {roc_auc_score(y, proba):.4f}")
    print(f"  average_precision{average_precision_score(y, proba):.4f}")
    print(f"  precision        {precision_score(y, pred, zero_division=0):.4f}")
    print(f"  recall           {recall_score(y, pred, zero_division=0):.4f}")
    print(f"  f1               {f1_score(y, pred, zero_division=0):.4f}")
    print(f"  positives predicted {pred.sum()} / {len(pred)} ; actual fraud {y.sum()}")


if __name__ == "__main__":
    main()
