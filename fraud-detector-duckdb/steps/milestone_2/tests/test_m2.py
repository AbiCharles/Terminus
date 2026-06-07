"""Tests for milestone 2 (Train Fraud Classifier).

Verifies the saved joblib model is a fitted GradientBoostingClassifier with the
spec hyperparameters, and that the logged model_metrics meet the acceptance
floors and match an independent retrain on the feature table.
"""
import math
import pathlib

import joblib
import pytest
from sklearn.ensemble import GradientBoostingClassifier

import _reference as ref


@pytest.fixture(scope="module")
def con():
    c = ref.connect(read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def metrics(con):
    rows = con.execute("SELECT metric, value FROM model_metrics").fetchall()
    return {metric: value for metric, value in rows}


class TestMilestone2:
    """Milestone 2: the trained classifier, its artifact, and its metrics."""

    def test_features_persist(self, con):
        """The milestone 1 `features` table must still exist (state persists)."""
        tables = {t[0] for t in con.execute("SHOW TABLES").fetchall()}
        assert "features" in tables, "features table missing — was milestone 1 completed?"

    def test_model_artifact_loads(self):
        """The joblib artifact must load as a fitted GBM with the spec hyperparameters."""
        path = pathlib.Path(ref.ARTIFACT_PATH)
        assert path.exists(), f"{path} does not exist"
        model = joblib.load(path)
        assert isinstance(model, GradientBoostingClassifier), "artifact is not a GradientBoostingClassifier"
        assert model.n_estimators == 150, "n_estimators must be 150"
        assert model.max_depth == 3, "max_depth must be 3"
        assert math.isclose(model.learning_rate, 0.1), "learning_rate must be 0.1"
        assert model.random_state == 42, "random_state must be 42"
        assert getattr(model, "n_features_in_", None) == 6, "model must be fit on the six features"

    def test_metrics_present_and_meet_floors(self, metrics):
        """model_metrics must hold the five metrics in [0,1] meeting the acceptance floors."""
        assert set(metrics) == {"roc_auc", "average_precision", "precision", "recall", "f1"}
        assert all(0.0 <= v <= 1.0 for v in metrics.values()), "metric values out of [0,1]"
        assert metrics["roc_auc"] >= 0.90, f"roc_auc {metrics['roc_auc']} below floor 0.90"
        assert metrics["average_precision"] >= 0.80, (
            f"average_precision {metrics['average_precision']} below floor 0.80"
        )

    def test_metrics_match_reference(self, con, metrics):
        """Logged metrics must match an independent retrain on the feature table (anti-fabrication)."""
        feats = con.execute("SELECT * FROM features").df()
        expected = ref.reference_metrics(feats)
        for key, value in expected.items():
            assert abs(metrics[key] - value) < 1e-4, (
                f"{key}: logged {metrics[key]:.5f} vs reference {value:.5f}"
            )
