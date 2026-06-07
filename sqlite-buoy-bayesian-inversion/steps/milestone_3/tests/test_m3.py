"""Tests for milestone 3 (Run Bayesian Inversion). Run alone with: pytest tests/test_m3.py

These tests verify that, for every calibrated buoy, /app/artifacts/<buoy_id>/posterior.json
reports the conjugate Gaussian posterior for offset and drift (mean, standard
deviation, 95% credible interval), the admitted observation count, and the pre/post
correction RMSE — all matched against an independent recomputation from the SQLite
store and the binding priors (_reference.py). A fleet summary aggregates the
per-buoy corrected RMSE.
"""

import json
from pathlib import Path

import pytest

import _reference

ARTIFACTS = Path("/app/artifacts")
RTOL = 1e-4


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
    """Milestone 3: conjugate Gaussian posterior and calibration metrics per buoy."""

    def test_observation_count(self, included, reference):
        """Each posterior must report the admitted observation count from the clean series."""
        for buoy in included:
            assert load(buoy)["n_observations"] == reference[buoy]["n_observations"]

    def test_posterior_offset_drift(self, included, reference):
        """Posterior mean and std of offset and drift must match the conjugate recomputation."""
        for buoy in included:
            got = load(buoy)["posterior"]
            exp = reference[buoy]["posterior"]
            for param in ("offset", "drift"):
                assert got[param]["mean"] == pytest.approx(exp[param]["mean"], rel=RTOL, abs=1e-9)
                assert got[param]["std"] == pytest.approx(exp[param]["std"], rel=RTOL, abs=1e-9)

    def test_credible_intervals(self, included, reference):
        """The 95% credible intervals must match the recomputed bounds and bracket the mean."""
        for buoy in included:
            got = load(buoy)
            exp = reference[buoy]
            for param in ("offset", "drift"):
                lo, hi = got["credible_interval_95"][param]
                elo, ehi = exp["credible_interval_95"][param]
                assert lo == pytest.approx(elo, rel=RTOL, abs=1e-9)
                assert hi == pytest.approx(ehi, rel=RTOL, abs=1e-9)
                assert lo < got["posterior"][param]["mean"] < hi

    def test_calibration_metrics(self, included, reference):
        """Pre- and post-correction RMSE must match, and correction must not worsen the residual."""
        for buoy in included:
            got = load(buoy)["calibration"]
            exp = reference[buoy]["calibration"]
            assert got["rmse_residual"] == pytest.approx(exp["rmse_residual"], rel=RTOL, abs=1e-9)
            assert got["corrected_rmse"] == pytest.approx(exp["corrected_rmse"], rel=RTOL, abs=1e-9)
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
        assert summary["fleet"]["mean_corrected_rmse"] == pytest.approx(mean_corrected, rel=RTOL, abs=1e-9)
