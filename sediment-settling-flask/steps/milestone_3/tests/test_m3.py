"""Tests for milestone 3 (Fit Sedimentation Model).
Run alone with: pytest tests/test_m3.py

Verifies /app/output/report.json reproduces the nonlinear fit, 95% CIs, derived
quantities, and residual metrics from an independent refit (/app/spec.md §4).
"""

import json
import math
from pathlib import Path

import pytest

import _reference

REPORT_PATH = Path("/app/output/report.json")
REQUIRED_KEYS = {"experiment_id", "h_inf_cm", "k_per_s", "h_inf_ci95", "k_ci95",
                 "initial_velocity_cm_s", "effective_diameter_um", "rmse", "r2", "n_obs"}


@pytest.fixture(scope="module")
def agent_report():
    assert REPORT_PATH.exists(), "/app/output/report.json does not exist — milestone 3 not completed"
    with REPORT_PATH.open() as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def reference_report():
    return _reference.fit()


class TestMilestone3:
    """Milestone 3: nonlinear fit, confidence intervals, derived quantities, residuals."""

    def test_prior_outputs_persist(self):
        """metadata.json and observations.csv from earlier milestones must still exist."""
        assert Path("/app/output/metadata.json").exists(), "metadata.json missing"
        assert Path("/app/output/observations.csv").exists(), "observations.csv missing"

    def test_required_keys(self, agent_report):
        """report.json must contain exactly the specified keys."""
        assert set(agent_report) == REQUIRED_KEYS, f"key mismatch: {set(agent_report) ^ REQUIRED_KEYS}"

    def test_n_obs_matches(self, agent_report, reference_report):
        """n_obs must equal the number of fitted (valid) observations."""
        assert agent_report["n_obs"] == reference_report["n_obs"]

    def test_parameters_match_reference(self, agent_report, reference_report):
        """Fitted H_inf and k must match the independent refit."""
        assert math.isclose(agent_report["h_inf_cm"], reference_report["h_inf_cm"], rel_tol=1e-3, abs_tol=1e-4)
        assert math.isclose(agent_report["k_per_s"], reference_report["k_per_s"], rel_tol=1e-3, abs_tol=1e-6)

    def test_confidence_intervals_match(self, agent_report, reference_report):
        """95% CI half-widths must match the independent refit."""
        assert math.isclose(agent_report["h_inf_ci95"], reference_report["h_inf_ci95"], rel_tol=5e-2, abs_tol=1e-4)
        assert math.isclose(agent_report["k_ci95"], reference_report["k_ci95"], rel_tol=5e-2, abs_tol=1e-6)

    def test_derived_and_residuals_match(self, agent_report, reference_report):
        """Derived velocity/diameter and residual metrics must match the reference."""
        assert math.isclose(agent_report["initial_velocity_cm_s"], reference_report["initial_velocity_cm_s"], rel_tol=1e-2, abs_tol=1e-4)
        assert math.isclose(agent_report["effective_diameter_um"], reference_report["effective_diameter_um"], rel_tol=1e-2, abs_tol=1e-2)
        assert math.isclose(agent_report["rmse"], reference_report["rmse"], rel_tol=5e-2, abs_tol=1e-3)
        assert math.isclose(agent_report["r2"], reference_report["r2"], rel_tol=0, abs_tol=1e-3)
