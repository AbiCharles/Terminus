"""Tests for milestone 2 (Train Discrete-Time Hazard Model).
Run alone with: pytest tests/test_m2.py

Verifies that the serialized model is a fitted LogisticRegression trained on the
person-period rows with the spec's design matrix and hyperparameters, by
independently retraining the reference model and comparing.
"""

from pathlib import Path

import duckdb
import joblib
import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

import _reference

DB_PATH = "/app/survival.duckdb"
MODEL_PATH = Path("/app/artifacts/survival_model.joblib")
# Structural tolerance: lbfgs converges only to its stopping tolerance, and the
# training-row order leaves ~2e-3 slack in the coefficients. The predicted-hazard
# check below (which is what actually drives the outputs) is the precise guard.
COEF_TOL = 1e-2
HAZARD_TOL = 5e-3


@pytest.fixture(scope="module")
def agent_model():
    assert MODEL_PATH.exists(), f"{MODEL_PATH} does not exist — milestone 2 not completed"
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def reference_model():
    return _reference.reference_model()


class TestMilestone2:
    """Milestone 2: the serialized discrete-time hazard model."""

    def test_person_period_persists(self):
        """The person_period table from milestone 1 must still exist (state persists)."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert "person_period" in tables, "person_period missing — was milestone 1 completed?"

    def test_model_is_fitted_logreg(self, agent_model):
        """The artifact must load as a fitted LogisticRegression with 7 coefficients."""
        assert isinstance(agent_model, LogisticRegression), "model must be a LogisticRegression"
        assert hasattr(agent_model, "coef_"), "model is not fitted"
        assert agent_model.coef_.shape[1] == len(_reference.FEATURES), (
            f"expected {len(_reference.FEATURES)} features, got {agent_model.coef_.shape[1]}"
        )

    def test_coefficients_match_reference(self, agent_model, reference_model):
        """Coefficients/intercept must match an independent retrain (anti-fabrication)."""
        assert np.allclose(agent_model.coef_, reference_model.coef_, atol=COEF_TOL), (
            "model coefficients differ from the reference discrete-time hazard fit"
        )
        assert np.allclose(agent_model.intercept_, reference_model.intercept_, atol=COEF_TOL), (
            "model intercept differs from the reference fit"
        )

    def test_predicted_hazards_match_reference(self, agent_model, reference_model):
        """Predicted hazards on the test design rows must match the reference model."""
        subjects = _reference.load_subjects()
        test = subjects[subjects["split"] == "test"].reset_index(drop=True)
        curves_design = test.loc[test.index.repeat(_reference.K)].copy()
        curves_design["period"] = np.tile(np.arange(1, _reference.K + 1), len(test))
        x = _reference.design(curves_design)
        h_agent = agent_model.predict_proba(x)[:, 1]
        h_ref = reference_model.predict_proba(x)[:, 1]
        assert np.allclose(h_agent, h_ref, atol=HAZARD_TOL), "predicted hazards differ from the reference model"
