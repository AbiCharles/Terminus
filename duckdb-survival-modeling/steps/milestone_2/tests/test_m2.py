"""Tests for milestone 2 (Multinomial Discrete-Time Hazard Model).
Run alone with: pytest tests/test_m2.py

Verifies the serialized model is a fitted 3-class LogisticRegression trained on the
person-period rows with the spec's design matrix, by independently retraining the
reference model and comparing coefficients and predicted cause-specific hazards.
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
# Structural tolerance: lbfgs converges only to its stopping tolerance and the
# training-row order leaves a few-1e-3 of slack in the multinomial coefficients.
# The predicted-hazard check below is the precise behavioral guard.
COEF_TOL = 1.5e-2
HAZARD_TOL = 5e-3


@pytest.fixture(scope="module")
def agent_model():
    assert MODEL_PATH.exists(), f"{MODEL_PATH} does not exist — milestone 2 not completed"
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def reference_model():
    return _reference.reference_model()


class TestMilestone2:
    """Milestone 2: the serialized multinomial discrete-time hazard model."""

    def test_person_period_persists(self):
        """The person_period table from milestone 1 must still exist (state persists)."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert "person_period" in tables, "person_period missing — was milestone 1 completed?"

    def test_model_is_three_class_logreg(self, agent_model):
        """The artifact must load as a fitted LogisticRegression over classes [0,1,2] with 7 features."""
        assert isinstance(agent_model, LogisticRegression), "model must be a LogisticRegression"
        assert hasattr(agent_model, "coef_"), "model is not fitted"
        assert list(agent_model.classes_) == [0, 1, 2], "model must be trained on the 3-class period_outcome"
        assert agent_model.coef_.shape[1] == len(_reference.FEATURES), (
            f"expected {len(_reference.FEATURES)} features, got {agent_model.coef_.shape[1]}"
        )

    def test_coefficients_match_reference(self, agent_model, reference_model):
        """Coefficients must match an independent multinomial retrain (anti-fabrication)."""
        assert np.allclose(agent_model.coef_, reference_model.coef_, atol=COEF_TOL), (
            "model coefficients differ from the reference multinomial hazard fit"
        )

    def test_cause_specific_hazards_match_reference(self, agent_model, reference_model):
        """Predicted cause-1 and cause-2 hazards on the test grid must match the reference model."""
        subjects, measurements = _reference.load_tables()
        test = subjects[subjects["split"] == "test"].reset_index(drop=True)
        import pandas as pd
        full_k = pd.Series(np.full(len(test), _reference.K), index=test.index)
        grid = _reference._locf_grid(test, measurements, full_k)
        x = _reference.design(grid)
        pa, pr = agent_model.predict_proba(x), reference_model.predict_proba(x)
        ca, cr = list(agent_model.classes_), list(reference_model.classes_)
        for cause in (1, 2):
            assert np.allclose(pa[:, ca.index(cause)], pr[:, cr.index(cause)], atol=HAZARD_TOL), (
                f"predicted cause-{cause} hazards differ from the reference model"
            )
