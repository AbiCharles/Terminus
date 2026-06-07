"""Tests for milestone 3 (Run Bayesian Inversion). Run alone with: pytest tests/test_m3.py

Verifies /app/artifacts/<buoy_id>/posterior.json reports the heteroscedastic,
three-parameter change-point conjugate Gaussian posterior (offset, drift,
drift_change) with means, standard deviations and 95% credible intervals, the
admitted observation count, the changepoint, and pre/post-correction RMSE — all
matched against an independent recomputation from the database and the binding
priors (_reference.py). Matching requires the agent to use the weighted (1/std^2)
GLS with the hinge regressor; an unweighted or two-parameter fit falls outside
tolerance. A fleet summary aggregates the per-buoy corrected RMSE.
"""

import json
from pathlib import Path

import pytest

import _reference

ARTIFACTS = Path("/app/artifacts")
PARAMS = ("offset", "drift", "drift_change")


@pytest.fixture(scope="module")
def included():
    ids = _reference.included_buoys()
    assert ids, "no calibrated buoys found"
    return ids


@pytest.fixture(scope="module")
def reference(included):
    return {b: _reference.posterior(b) for b in included}


def load(buoy):
    path = ARTIFACTS / buoy / "posterior.json"
    assert path.exists(), f"{buoy} missing posterior.json — milestone 3 not completed"
    return json.loads(path.read_text())


class TestMilestone3:
    """Milestone 3: heteroscedastic three-parameter change-point posterior per buoy."""

    def test_observation_count(self, included, reference):
        """Each posterior must report the admitted observation count from the clean series."""
        for buoy in included:
            assert load(buoy)["n_observations"] == reference[buoy]["n_observations"]

    def test_changepoint(self, included, reference):
        """Each posterior must report the changepoint in elapsed days."""
        for buoy in included:
            assert load(buoy)["changepoint_t_days"] == pytest.approx(
                reference[buoy]["changepoint_t_days"], abs=1e-6
            )

    def test_posterior_offset_drift(self, included, reference):
        """Posterior mean/std of offset, drift and drift_change must match the weighted GLS recomputation."""
        for buoy in included:
            got = load(buoy)["posterior"]
            exp = reference[buoy]["posterior"]
            for p in PARAMS:
                assert got[p]["mean"] == pytest.approx(exp[p]["mean"], rel=1e-3, abs=1e-9), f"{buoy}.{p}.mean"
                assert got[p]["std"] == pytest.approx(exp[p]["std"], rel=1e-2, abs=1e-9), f"{buoy}.{p}.std"

    def test_credible_intervals(self, included, reference):
        """The 95% credible intervals must match the recomputed bounds and bracket the mean."""
        for buoy in included:
            got = load(buoy)
            exp = reference[buoy]
            for p in PARAMS:
                lo, hi = got["credible_interval_95"][p]
                elo, ehi = exp["credible_interval_95"][p]
                assert lo == pytest.approx(elo, rel=1e-3, abs=1e-9), f"{buoy}.{p}.lo"
                assert hi == pytest.approx(ehi, rel=1e-3, abs=1e-9), f"{buoy}.{p}.hi"
                assert lo < got["posterior"][p]["mean"] < hi

    def test_calibration_metrics(self, included, reference):
        """Pre/post-correction RMSE must match, and correction must not worsen the residual."""
        for buoy in included:
            got = load(buoy)["calibration"]
            exp = reference[buoy]["calibration"]
            assert got["rmse_residual"] == pytest.approx(exp["rmse_residual"], rel=1e-3, abs=1e-9)
            assert got["corrected_rmse"] == pytest.approx(exp["corrected_rmse"], rel=1e-3, abs=1e-9)
            assert got["corrected_rmse"] <= got["rmse_residual"] + 1e-9

    def test_fleet_summary(self, included, reference):
        """summary.json must aggregate the per-buoy corrected RMSE over the calibrated fleet."""
        path = ARTIFACTS / "summary.json"
        assert path.exists(), "summary.json missing"
        summary = json.loads(path.read_text())
        listed = {b["buoy_id"] for b in summary["buoys"]}
        assert listed == set(included), f"summary buoys {listed} != calibrated {set(included)}"
        assert summary["fleet"]["n_buoys"] == len(included)
        mean_corrected = sum(reference[b]["calibration"]["corrected_rmse"] for b in included) / len(included)
        assert summary["fleet"]["mean_corrected_rmse"] == pytest.approx(mean_corrected, rel=1e-3, abs=1e-9)
