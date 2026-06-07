# Fraud Detection Feature & Model Specification (v1)

This document specifies the data contracts for the account-fraud detection pipeline. The pipeline
operates entirely on the DuckDB database at `/app/fraud.duckdb`. All tables described below live in
that database. Timestamps are UTC; "the account" means rows sharing the same `account_id`, and
"order" always means ascending `ts`.

## 1. Source table: `transactions`

One row per card transaction. This table is the sole input and must not be modified.

| column | type | description |
|---|---|---|
| `transaction_id` | BIGINT | unique transaction identifier |
| `account_id` | INTEGER | account the transaction belongs to |
| `ts` | TIMESTAMP | transaction time (unique and strictly increasing within an account) |
| `amount` | DOUBLE | transaction amount in dollars |
| `merchant_category` | VARCHAR | merchant category |
| `is_fraud` | INTEGER | label: 1 if the transaction was fraudulent, else 0 |
| `split` | VARCHAR | `train` or `score` (temporal split; an account's later transactions are `score`) |

## 2. Feature table: `features`

Exactly one row per transaction (same cardinality as `transactions`). Behavioural features are
computed per account over the transaction history. Each feature is defined relative to the
*current* transaction; windows are partitioned by `account_id` and ordered by `ts`.

| column | type | definition |
|---|---|---|
| `transaction_id` | BIGINT | from `transactions` |
| `account_id` | INTEGER | from `transactions` |
| `ts` | TIMESTAMP | from `transactions` |
| `is_fraud` | INTEGER | from `transactions` |
| `split` | VARCHAR | from `transactions` |
| `prev_txn_gap_sec` | DOUBLE | seconds between this transaction and the account's immediately preceding transaction. For the account's first transaction this is `0`. |
| `acct_txn_index` | BIGINT | count of the account's transactions that precede this one (`0` for the first transaction). |
| `amt_count_1h` | BIGINT | number of the account's transactions whose `ts` falls in the trailing one-hour window **up to and including** this transaction — that is, with `ts` in `[this.ts - 1 hour, this.ts]`. Counts this transaction itself. |
| `amt_sum_24h` | DOUBLE | sum of `amount` over the account's transactions whose `ts` falls in the trailing twenty-four-hour window **up to and including** this transaction (`ts` in `[this.ts - 24 hours, this.ts]`). |
| `amt_avg_prev5` | DOUBLE | average `amount` over the account's up-to-five transactions **immediately preceding** this one (this transaction is **excluded**). When there are no preceding transactions, `0`. |
| `amt_ratio_prev5` | DOUBLE | `amount / amt_avg_prev5`. When `amt_avg_prev5` is `0`, this is `0`. |

All time-window bounds are inclusive of both endpoints. Because timestamps are unique within an
account, the trailing windows never include a future transaction.

## 3. Model

A single `sklearn.ensemble.GradientBoostingClassifier` with these hyperparameters:

- `n_estimators = 150`
- `max_depth = 3`
- `learning_rate = 0.1`
- `random_state = 42`

Inputs are the six numeric feature columns, in this order: `prev_txn_gap_sec`, `acct_txn_index`,
`amt_count_1h`, `amt_sum_24h`, `amt_avg_prev5`, `amt_ratio_prev5`. The target is `is_fraud`. The
model is fit on the `features` rows with `split = 'train'` and evaluated on the rows with
`split = 'score'`.

The fitted estimator is persisted with `joblib` to `/app/artifacts/fraud_model.joblib`.

### Evaluation metrics

Computed on the `score` split, using a decision threshold of `0.5` on the positive-class
probability for the threshold-dependent metrics:

| metric name | meaning |
|---|---|
| `roc_auc` | area under the ROC curve (uses probabilities) |
| `average_precision` | average precision / area under the PR curve (uses probabilities) |
| `precision` | precision of the positive (fraud) class at threshold 0.5 |
| `recall` | recall of the positive (fraud) class at threshold 0.5 |
| `f1` | F1 of the positive (fraud) class at threshold 0.5 |

Acceptance floors for a valid model: `roc_auc >= 0.90` and `average_precision >= 0.80`.

### Metrics table: `model_metrics`

| column | type | description |
|---|---|---|
| `metric` | VARCHAR | metric name (one of the five above) |
| `value` | DOUBLE | metric value on the `score` split |

One row per metric (five rows total).

## 4. Scoring CLI: `/app/score.py`

A command-line program that loads the persisted model and the `features` rows with
`split = 'score'`, computes the positive-class fraud probability for each, and writes the results
into a `scored_transactions` table. Running it must be idempotent (a re-run reproduces the same
table contents).

### Output table: `scored_transactions`

| column | type | description |
|---|---|---|
| `transaction_id` | BIGINT | the scored transaction |
| `fraud_probability` | DOUBLE | model positive-class probability, in `[0, 1]` |
| `fraud_prediction` | INTEGER | `1` if `fraud_probability >= 0.5`, else `0` |

One row per `score`-split transaction.
