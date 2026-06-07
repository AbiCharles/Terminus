"""Tests for milestone 3 (Fit Sedimentation Model).

Verifies /app/output/report.json and report.csv hold the two-phase breakpoint,
parameter estimates, 95% CIs, derived diameter, and residual metrics matching an
independent grid-search refit.
"""
import json
import pathlib

import pandas as pd
import pytest

import _reference as ref

REPORT_JSON = pathlib.Path(ref.OUT_DIR) / "report.json"
REPORT_CSV = pathlib.Path(ref.OUT_DIR) / "report.csv"

TOL = {
    "t_c_s": 0.5, "v1_cm_per_s": 1e-3, "h_inf_cm": 1e-3, "k_per_s": 1e-4,
    "v1_cm_per_s_ci95": 1e-3, "h_inf_cm_ci95": 1e-3, "k_per_s_ci95": 1e-4,
    "effective_diameter_um": 0.5, "rmse_cm": 1e-4, "r2": 1e-4, "n_obs": 0.5,
}


@pytest.fixture(scope="module")
def report():
    assert REPORT_JSON.exists(), f"{REPORT_JSON} does not exist"
    with REPORT_JSON.open() as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def expected():
    return ref.reference_fit(ref.TARGET_ID)


def _flat(report):
    return {
        "t_c_s": report["breakpoint"]["t_c_s"],
        "v1_cm_per_s": report["parameters"]["v1_cm_per_s"],
        "h_inf_cm": report["parameters"]["h_inf_cm"],
        "k_per_s": report["parameters"]["k_per_s"],
        "v1_cm_per_s_ci95": report["ci95"]["v1_cm_per_s"],
        "h_inf_cm_ci95": report["ci95"]["h_inf_cm"],
        "k_per_s_ci95": report["ci95"]["k_per_s"],
        "effective_diameter_um": report["derived"]["effective_diameter_um"],
        "rmse_cm": report["residuals"]["rmse_cm"],
        "r2": report["residuals"]["r2"],
        "n_obs": report["residuals"]["n_obs"],
    }


class TestMilestone3:
    """Milestone 3: the two-phase fitted-model report."""

    def test_prior_artifacts_persist(self):
        """Milestone 1/2 outputs must still exist (state persists)."""
        assert (pathlib.Path(ref.OUT_DIR) / "config.json").exists()
        assert (pathlib.Path(ref.OUT_DIR) / "observations.csv").exists()

    def test_report_schema(self, report):
        """report.json must carry breakpoint, parameters, ci95, derived and residuals."""
        assert report["experiment_id"] == ref.TARGET_ID
        assert "t_c_s" in report["breakpoint"]
        assert set(report["parameters"]) == {"v1_cm_per_s", "h_inf_cm", "k_per_s"}
        assert set(report["ci95"]) == {"v1_cm_per_s", "h_inf_cm", "k_per_s"}
        assert "effective_diameter_um" in report["derived"]
        assert {"rmse_cm", "r2", "n_obs"} <= set(report["residuals"])

    def test_report_matches_reference(self, report, expected):
        """All reported quantities must match the independent grid-search refit."""
        flat = _flat(report)
        for key, exp in expected.items():
            assert abs(float(flat[key]) - float(exp)) <= TOL[key], (
                f"{key}: reported {flat[key]} vs reference {exp}"
            )

    def test_report_csv_consistent(self, expected):
        """report.csv must contain the same quantities/values as the reference."""
        assert REPORT_CSV.exists(), f"{REPORT_CSV} does not exist"
        table = pd.read_csv(REPORT_CSV)
        assert list(table.columns) == ["quantity", "value"], "wrong report.csv header"
        values = dict(zip(table["quantity"], table["value"]))
        for key, exp in expected.items():
            assert key in values, f"report.csv missing {key}"
            assert abs(float(values[key]) - float(exp)) <= TOL[key], (
                f"report.csv {key}: {values[key]} vs reference {exp}"
            )
