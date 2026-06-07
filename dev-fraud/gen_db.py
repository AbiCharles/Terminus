"""Generate the synthetic transaction dataset for the fraud-detector task.

Design:
  * ~800 accounts, ~40k transactions, each account a time-ordered sequence with
    STRICTLY INCREASING whole-second timestamps (so DuckDB time-RANGE windows have
    no tie ambiguity and a pandas recompute can match exactly).
  * Normal behaviour: long inter-arrival gaps (hours-days), lognormal amounts.
  * Fraud is injected as BURSTS: short runs of transactions seconds-minutes apart
    with inflated amounts. This makes the window features (1h velocity, short
    inter-txn gap, amount-vs-recent-average ratio) genuinely predictive while
    leaving enough noise that the model is not trivially perfect.
  * Temporal split per account: first 70% of each account's transactions -> train,
    last 30% -> score (realistic "predict the future" split; score rows still have
    full prior history for windowing).
"""
import os

import duckdb
import numpy as np
import pandas as pd

RNG = np.random.default_rng(7919)
N_ACCOUNTS = 800
MERCHANTS = ["grocery", "restaurant", "gas", "online", "electronics", "travel", "atm"]
BASE_EPOCH = 1_577_836_800  # 2020-01-01T00:00:00Z, in seconds

rows = []
txn_id = 0
for acct in range(N_ACCOUNTS):
    n_txn = int(RNG.integers(30, 71))
    acct_mu = RNG.uniform(3.0, 4.6)  # lognormal mean param -> ~$20-$100 typical
    t = BASE_EPOCH + int(RNG.integers(0, 60 * 60 * 24 * 365))  # account start
    seq = []
    i = 0
    while i < n_txn:
        # normal transaction
        gap = int(RNG.exponential(60 * 60 * 30))  # ~1.25 day mean
        t += max(gap, 1)
        amount = float(np.round(RNG.lognormal(acct_mu, 0.5), 2))
        merchant = MERCHANTS[int(RNG.integers(0, len(MERCHANTS)))]
        is_fraud = 0
        # rare normal high-amount outlier (adds false-positive-looking signal)
        if RNG.random() < 0.02:
            amount = float(np.round(amount * RNG.uniform(3, 6), 2))
        seq.append((t, amount, merchant, is_fraud))
        i += 1
        # legitimate rapid burst (non-fraud) — creates overlapping velocity signal
        if i < n_txn - 3 and RNG.random() < 0.03:
            legit = int(RNG.integers(2, 5))
            for _ in range(legit):
                if i >= n_txn:
                    break
                t += int(RNG.integers(60, 1800))
                amount = float(np.round(RNG.lognormal(acct_mu, 0.5), 2))
                merchant = MERCHANTS[int(RNG.integers(0, len(MERCHANTS)))]
                seq.append((t, amount, merchant, 0))
                i += 1
        # inject a fraud burst occasionally
        if i < n_txn - 3 and RNG.random() < 0.02:
            burst = int(RNG.integers(2, 6))
            base_amt = np.exp(acct_mu)
            for _ in range(burst):
                if i >= n_txn:
                    break
                t += int(RNG.integers(8, 400))  # seconds-minutes apart
                # most fraud is inflated; a minority looks normal (velocity only)
                if RNG.random() < 0.6:
                    amount = float(np.round(base_amt * RNG.uniform(2.5, 7.0), 2))
                else:
                    amount = float(np.round(RNG.lognormal(acct_mu, 0.5), 2))
                merchant = MERCHANTS[int(RNG.integers(3, len(MERCHANTS)))]  # online/electronics/travel/atm
                seq.append((t, amount, merchant, 1))
                i += 1

    seq.sort(key=lambda r: r[0])
    # de-duplicate timestamps within the account (strictly increasing seconds)
    last_t = None
    fixed = []
    for (tt, amount, merchant, isf) in seq:
        if last_t is not None and tt <= last_t:
            tt = last_t + 1
        last_t = tt
        fixed.append((tt, amount, merchant, isf))

    cutoff = int(len(fixed) * 0.7)
    for idx, (tt, amount, merchant, isf) in enumerate(fixed):
        rows.append(
            (txn_id, acct, tt, amount, merchant, isf, "train" if idx < cutoff else "score")
        )
        txn_id += 1

df = pd.DataFrame(
    rows,
    columns=["transaction_id", "account_id", "ts_epoch", "amount", "merchant_category", "is_fraud", "split"],
)
df["ts"] = pd.to_datetime(df["ts_epoch"], unit="s")
df = df[["transaction_id", "account_id", "ts", "amount", "merchant_category", "is_fraud", "split"]]

if __name__ == "__main__":
    out = "fraud.duckdb"
    if os.path.exists(out):
        os.remove(out)
    con = duckdb.connect(out)
    con.execute(
        """
        CREATE TABLE transactions (
            transaction_id BIGINT PRIMARY KEY,
            account_id INTEGER,
            ts TIMESTAMP,
            amount DOUBLE,
            merchant_category VARCHAR,
            is_fraud INTEGER,
            split VARCHAR
        )
        """
    )
    con.execute("INSERT INTO transactions SELECT * FROM df")
    con.close()
    print("rows", len(df))
    print("fraud_rate_overall", round(df.is_fraud.mean(), 4))
    print(df.groupby("split").agg(n=("is_fraud", "size"), fraud_rate=("is_fraud", "mean")).round(4))
    print("accounts", df.account_id.nunique(), "| file MB", round(os.path.getsize(out) / 1e6, 2))
