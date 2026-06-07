"""Tests for milestone 3 (Survival Curves, Risk Scores & Metrics).
Run alone with: pytest tests/test_m3.py

Verifies the survival_curves / risk_scores / model_metrics tables, the predictions
file, and model-reload inference against an independent recomputation (/app/spec.md §5).
"""

from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
import pytest

import _reference

DB_PATH = "/app/survival.duckdb"
MODEL_PATH = Path("/app/artifacts/survival_model.joblib")
PRED_PATH = Path("/app/artifacts/predictions.csv")
METRIC_TOL = 5e-3
C_INDEX_FLOOR = 0.72
IBS_CEILING = 0.18


@pytest.fixture(scope="module")
def ref():
    return _reference.reference_outputs()


@pytest.fixture(scope="module")
def tables():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        names = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        out = {}
        for t in ("survival_curves", "risk_scores", "model_metrics"):
            if t in names:
                out[t] = con.execute(f"SELECT * FROM {t}").df()
    finally:
        con.close()
    return out


class TestMilestone3:
    """Milestone 3: survival curves, risk scores, and evaluation metrics."""

    def test_prior_artifacts_persist(self):
        """Milestone 1/2 artifacts (person_period table, model file) must still exist."""
        assert MODEL_PATH.exists(), "survival_model.joblib missing — was milestone 2 completed?"
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert "person_period" in tables, "person_period missing — was milestone 1 completed?"

    def test_output_tables_exist(self, tables):
        """survival_curves, risk_scores and model_metrics tables must all exist."""
        for t in ("survival_curves", "risk_scores", "model_metrics"):
            assert t in tables, f"table {t} was not created"

    def test_survival_curves_valid(self, tables, ref):
        """Curves: one row per test subject per period, probabilities in [0,1], non-increasing."""
        sc = tables["survival_curves"]
        assert {"subject_id", "period", "survival_prob"} <= set(sc.columns)
        assert len(sc) == len(ref["test"]) * _reference.K, "unexpected survival_curves row count"
        assert sc["survival_prob"].between(0.0, 1.0).all(), "survival_prob outside [0, 1]"
        sc = sc.sort_values(["subject_id", "period"])
        diffs = sc.groupby("subject_id")["survival_prob"].diff().dropna()
        assert (diffs <= 1e-9).all(), "survival_prob must be non-increasing within each subject"

    def test_risk_scores_valid(self, tables, ref):
        """Risk scores: one per test subject, in [0,1], equal to 1 - S(K) from the curves."""
        rs = tables["risk_scores"]
        assert {"subject_id", "risk_score"} <= set(rs.columns)
        assert len(rs) == len(ref["test"]), "unexpected risk_scores row count"
        assert rs["risk_score"].between(0.0, 1.0).all(), "risk_score outside [0, 1]"
        sc = tables["survival_curves"]
        s_at_k = sc[sc["period"] == _reference.K][["subject_id", "survival_prob"]]
        merged = rs.merge(s_at_k, on="subject_id")
        assert np.allclose(merged["risk_score"], 1.0 - merged["survival_prob"], atol=1e-6), (
            "risk_score must equal 1 - S(K)"
        )

    def test_metrics_match_reference_and_floors(self, tables, ref):
        """model_metrics must hold c_index and integrated_brier_score, matching the reference and floors."""
        mm = tables["model_metrics"]
        assert {"metric", "value"} <= set(mm.columns)
        vals = dict(zip(mm["metric"], mm["value"]))
        assert "c_index" in vals and "integrated_brier_score" in vals, "missing required metrics"
        assert abs(vals["c_index"] - ref["c_index"]) <= METRIC_TOL, (
            f"c_index {vals['c_index']:.4f} differs from reference {ref['c_index']:.4f}"
        )
        assert abs(vals["integrated_brier_score"] - ref["integrated_brier_score"]) <= METRIC_TOL, (
            f"integrated_brier_score {vals['integrated_brier_score']:.4f} differs from reference "
            f"{ref['integrated_brier_score']:.4f}"
        )
        assert vals["c_index"] >= C_INDEX_FLOOR, f"c_index {vals['c_index']:.4f} below floor {C_INDEX_FLOOR}"
        assert vals["integrated_brier_score"] <= IBS_CEILING, (
            f"integrated_brier_score {vals['integrated_brier_score']:.4f} above ceiling {IBS_CEILING}"
        )

    def test_predictions_file(self, ref):
        """predictions.csv must exist with the right header, one row per test subject, consistent values."""
        assert PRED_PATH.exists(), "predictions.csv missing"
        preds = pd.read_csv(PRED_PATH)
        assert list(preds.columns) == ["subject_id", "risk_score", "survival_prob_at_K"], (
            "predictions.csv header must be subject_id,risk_score,survival_prob_at_K"
        )
        assert len(preds) == len(ref["test"]), "predictions.csv row count must equal test subject count"
        assert np.allclose(preds["risk_score"], 1.0 - preds["survival_prob_at_K"], atol=1e-6), (
            "risk_score must equal 1 - survival_prob_at_K"
        )

    def test_model_reload_inference(self, tables):
        """Reloading the saved model must reproduce the written survival_curves."""
        model = joblib.load(MODEL_PATH)
        test = _reference.load_subjects()
        test = test[test["split"] == "test"].reset_index(drop=True)
        recomputed = _reference.survival_curves(model, test)
        agent = tables["survival_curves"][["subject_id", "period", "survival_prob"]]
        merged = recomputed.merge(agent, on=["subject_id", "period"], suffixes=("_ref", "_agent"))
        assert len(merged) == len(recomputed), "survival_curves keys do not align with the reloaded model"
        assert np.allclose(merged["survival_prob_ref"], merged["survival_prob_agent"], atol=1e-6), (
            "written survival_prob values are not reproduced by the reloaded model"
        )
