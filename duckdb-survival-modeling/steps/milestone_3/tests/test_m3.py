"""Tests for milestone 3 (CIF Curves, Risk Scores & Competing-Risks Metrics).
Run alone with: pytest tests/test_m3.py

Verifies cif_curves / risk_scores / model_metrics, the predictions file, and
model-reload inference against an independent recomputation (/app/spec.md §5).
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
C_INDEX_FLOOR = 0.62
IBS_CEILING = 0.18


@pytest.fixture(scope="module")
def ref():
    return _reference.reference_outputs()


@pytest.fixture(scope="module")
def tables():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        names = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        out = {t: con.execute(f"SELECT * FROM {t}").df()
               for t in ("cif_curves", "risk_scores", "model_metrics") if t in names}
    finally:
        con.close()
    return out


class TestMilestone3:
    """Milestone 3: cumulative incidence curves, risk scores, and metrics."""

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
        """cif_curves, risk_scores and model_metrics tables must all exist."""
        for t in ("cif_curves", "risk_scores", "model_metrics"):
            assert t in tables, f"table {t} was not created"

    def test_cif_curves_valid(self, tables, ref):
        """CIFs non-decreasing, survival non-increasing, all in [0,1], and cif1+cif2+survival=1."""
        cc = tables["cif_curves"]
        assert {"subject_id", "period", "cif1", "cif2", "survival_prob"} <= set(cc.columns)
        assert len(cc) == len(ref["test"]) * _reference.K, "unexpected cif_curves row count"
        for col in ("cif1", "cif2", "survival_prob"):
            assert cc[col].between(-1e-9, 1 + 1e-9).all(), f"{col} outside [0,1]"
        total = cc["cif1"] + cc["cif2"] + cc["survival_prob"]
        assert np.allclose(total, 1.0, atol=1e-6), "cif1 + cif2 + survival_prob must equal 1"
        cc = cc.sort_values(["subject_id", "period"])
        assert (cc.groupby("subject_id")["cif1"].diff().dropna() >= -1e-9).all(), "cif1 must be non-decreasing"
        assert (cc.groupby("subject_id")["survival_prob"].diff().dropna() <= 1e-9).all(), (
            "survival_prob must be non-increasing"
        )

    def test_risk_scores_valid(self, tables, ref):
        """risk_score must be CIF_1(K) per test subject."""
        rs = tables["risk_scores"]
        assert {"subject_id", "risk_score"} <= set(rs.columns)
        assert len(rs) == len(ref["test"]), "unexpected risk_scores row count"
        cif1_k = tables["cif_curves"]
        cif1_k = cif1_k[cif1_k["period"] == _reference.K][["subject_id", "cif1"]]
        merged = rs.merge(cif1_k, on="subject_id")
        assert np.allclose(merged["risk_score"], merged["cif1"], atol=1e-6), "risk_score must equal CIF_1(K)"

    def test_metrics_match_reference_and_floors(self, tables, ref):
        """model_metrics must hold c_index and integrated_brier_score, matching reference and floors."""
        vals = dict(zip(tables["model_metrics"]["metric"], tables["model_metrics"]["value"]))
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
        """predictions.csv must have the right header, one row per test subject, and CIFs+S summing to 1."""
        assert PRED_PATH.exists(), "predictions.csv missing"
        preds = pd.read_csv(PRED_PATH)
        assert list(preds.columns) == ["subject_id", "cif1_at_K", "cif2_at_K", "survival_prob_at_K"], (
            "predictions.csv header must be subject_id,cif1_at_K,cif2_at_K,survival_prob_at_K"
        )
        assert len(preds) == len(ref["test"]), "predictions.csv row count must equal test subject count"
        total = preds["cif1_at_K"] + preds["cif2_at_K"] + preds["survival_prob_at_K"]
        assert np.allclose(total, 1.0, atol=1e-6), "cif1_at_K + cif2_at_K + survival_prob_at_K must equal 1"

    def test_model_reload_inference(self, tables):
        """Reloading the saved model must reproduce the written cif_curves."""
        model = joblib.load(MODEL_PATH)
        subjects, measurements = _reference.load_tables()
        test = subjects[subjects["split"] == "test"].reset_index(drop=True)
        recomputed = _reference.cif_curves(model, test, measurements)
        agent = tables["cif_curves"][["subject_id", "period", "cif1", "cif2", "survival_prob"]]
        merged = recomputed.merge(agent, on=["subject_id", "period"], suffixes=("_ref", "_agent"))
        assert len(merged) == len(recomputed), "cif_curves keys do not align with the reloaded model"
        for col in ("cif1", "cif2", "survival_prob"):
            assert np.allclose(merged[f"{col}_ref"], merged[f"{col}_agent"], atol=1e-6), (
                f"written {col} values are not reproduced by the reloaded model"
            )
