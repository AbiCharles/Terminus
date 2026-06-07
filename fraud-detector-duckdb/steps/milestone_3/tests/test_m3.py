"""Tests for milestone 3 (Score Transactions CLI).

Verifies the scored_transactions table has one valid row per score-split
transaction, predictions follow the 0.5 threshold, and probabilities match the
saved model applied to the score-split features.
"""
import pathlib

import joblib
import numpy as np
import pytest

import _reference as ref


@pytest.fixture(scope="module")
def con():
    c = ref.connect(read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def scored(con):
    return con.execute("SELECT * FROM scored_transactions ORDER BY transaction_id").df()


class TestMilestone3:
    """Milestone 3: the batch-scoring CLI output."""

    def test_prior_artifacts_persist(self, con):
        """Milestone 1/2 artifacts must persist (features + model_metrics tables, model file)."""
        tables = {t[0] for t in con.execute("SHOW TABLES").fetchall()}
        assert {"features", "model_metrics"}.issubset(tables), "prior tables missing"
        assert pathlib.Path(ref.ARTIFACT_PATH).exists(), "model artifact missing"

    def test_score_cli_exists(self):
        """The scoring CLI must exist at /app/score.py (spec §4)."""
        assert pathlib.Path("/app/score.py").exists(), "/app/score.py was not created"

    def test_scored_table_shape(self, scored):
        """scored_transactions must have one valid row per score-split transaction."""
        required = {"transaction_id", "fraud_probability", "fraud_prediction"}
        assert required.issubset(set(scored.columns)), "scored_transactions missing columns"
        assert len(scored) == ref.SCORE_COUNT, "must score every score-split transaction"
        assert scored["fraud_probability"].between(0.0, 1.0).all(), "probabilities out of [0,1]"
        assert set(np.unique(scored["fraud_prediction"])).issubset({0, 1}), "predictions not binary"

    def test_predictions_follow_threshold(self, scored):
        """fraud_prediction must equal (fraud_probability >= 0.5)."""
        expected = (scored["fraud_probability"].to_numpy() >= 0.5).astype(int)
        got = scored["fraud_prediction"].to_numpy().astype(int)
        assert np.array_equal(got, expected), "fraud_prediction does not follow the 0.5 threshold"

    def test_probabilities_match_model(self, con, scored):
        """Probabilities must match the saved model applied to the score-split features."""
        model = joblib.load(ref.ARTIFACT_PATH)
        feats = con.execute(
            "SELECT * FROM features WHERE split = 'score' ORDER BY transaction_id"
        ).df()
        expected = model.predict_proba(feats[ref.FEATURES])[:, 1]
        got = scored.sort_values("transaction_id")["fraud_probability"].to_numpy()
        assert np.abs(expected - got).max() < 1e-9, "scored probabilities do not match the model"
