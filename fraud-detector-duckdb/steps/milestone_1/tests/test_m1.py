"""Tests for milestone 1 (Create DuckDB Feature Store).

Verifies that /app/fraud.duckdb gained a `features` table whose values match an
independent pandas recompute of the spec's window definitions, and that the
source `transactions` table was not modified.
"""
import numpy as np
import pytest

import _reference as ref


@pytest.fixture(scope="module")
def con():
    c = ref.connect(read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def agent_features(con):
    return con.execute("SELECT * FROM features ORDER BY transaction_id").df()


class TestMilestone1:
    """Milestone 1: the DuckDB feature store built from SQL window functions."""

    def test_raw_transactions_intact(self, con):
        """The source `transactions` table must be unmodified (row count + checksums)."""
        n = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        assert n == ref.TXN_COUNT, f"transactions row count changed: {n}"
        amount_sum = con.execute("SELECT round(sum(amount), 2) FROM transactions").fetchone()[0]
        assert abs(amount_sum - ref.AMOUNT_SUM) < 0.01, "transactions.amount altered"
        fraud_sum = con.execute("SELECT sum(is_fraud) FROM transactions").fetchone()[0]
        assert fraud_sum == ref.FRAUD_SUM, "transactions.is_fraud altered"

    def test_features_table_exists(self, con):
        """A `features` table must exist in the database."""
        tables = {t[0] for t in con.execute("SHOW TABLES").fetchall()}
        assert "features" in tables, "features table was not created"

    def test_features_schema_and_cardinality(self, agent_features):
        """features must carry the required columns and exactly one row per transaction."""
        required = {"transaction_id", "account_id", "ts", "is_fraud", "split", *ref.FEATURES}
        missing = required - set(agent_features.columns)
        assert not missing, f"features missing columns: {missing}"
        assert len(agent_features) == ref.TXN_COUNT, "features must have one row per transaction"

    def test_feature_values_match_reference(self, con, agent_features):
        """Every feature value must match the independent recompute of the spec windows."""
        ref_df = ref.compute_reference_features(con)
        a = agent_features.set_index("transaction_id").sort_index()
        r = ref_df.set_index("transaction_id").sort_index()
        for col in ("acct_txn_index", "amt_count_1h"):
            assert np.array_equal(a[col].to_numpy(float), r[col].to_numpy(float)), (
                f"{col} does not match the reference window computation"
            )
        for col in ("prev_txn_gap_sec", "amt_sum_24h", "amt_avg_prev5", "amt_ratio_prev5"):
            d = float(np.abs(a[col].to_numpy(float) - r[col].to_numpy(float)).max())
            assert d < 1e-6, f"{col} max abs diff {d:.3e} vs reference"
