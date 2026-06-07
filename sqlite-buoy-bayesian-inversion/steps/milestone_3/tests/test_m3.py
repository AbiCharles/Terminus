"""Tests for milestone 3 (Run Bayesian Inversion). Run alone with: pytest tests/test_m3.py

Verifies /app/artifacts/<buoy_id>/posterior.json reports the heteroscedastic,
three-parameter change-point conjugate Gaussian posterior (offset, drift,
drift_change) with means, standard deviations and 95% credible intervals, the
admitted observation count, the changepoint, and pre/post-correction RMSE — all
matched against an independent numpy recomputation from the database and the binding
priors (_reference.py). Matching requires the weighted (1/std^2) GLS with the hinge
regressor; an unweighted or two-parameter fit falls outside tolerance.

The §13 acceptance gate (drift_change credible interval excludes zero) must partition
the fleet into accepted/rejected, recorded in /app/artifacts/summary.json. Accepted
buoys' correction models must be registered in /app/artifacts/registry.json (posterior
means as coefficients) and be queryable through the program's `predict` subcommand,
which must return offset + drift*t + drift_change*hinge; rejected buoys must not be
registered. A fleet summary aggregates the per-buoy corrected RMSE.
"""

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

import _reference

ARTIFACTS = Path("/app/artifacts")
BINARY = "/app/buoy_calibrate"
PARAMS = ("offset", "drift", "drift_change")


@pytest.fixture(scope="module")
def included():
    ids = _reference.included_buoys()
    assert ids, "no calibrated buoys found"
    return ids


@pytest.fixture(scope="module")
def reference(included):
    return {b: _reference.posterior(b) for b in included}


@pytest.fixture(scope="module")
def gate(included):
    """Per-buoy acceptance from the §13 gate (drift_change CI excludes zero)."""
    return {b: _reference.accepted(b) for b in included}


@pytest.fixture(scope="module")
def summary():
    path = ARTIFACTS / "summary.json"
    assert path.exists(), "summary.json missing — milestone 3 not completed"
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def registry():
    path = ARTIFACTS / "registry.json"
    assert path.exists(), "registry.json missing — accepted models were not registered"
    return json.loads(path.read_text())


def load(buoy):
    path = ARTIFACTS / buoy / "posterior.json"
    assert path.exists(), f"{buoy} missing posterior.json — milestone 3 not completed"
    return json.loads(path.read_text())


def predict(buoy, t, hinge):
    """Query the registered correction model through the program's predict subcommand."""
    out = subprocess.run(
        [BINARY, "predict", "--buoy", buoy, "--t", repr(float(t)), "--hinge", repr(float(hinge))],
        capture_output=True, text=True,
    )
    assert out.returncode == 0, f"predict failed for {buoy}: {out.stderr.strip()}"
    return float(out.stdout.strip())


class TestMilestone3:
    """Milestone 3: heteroscedastic three-parameter change-point posterior per buoy."""

    def test_observation_count(self, included, reference):
        """Each posterior must report buoy_id, sensor_type and the admitted observation count."""
        for buoy in included:
            p = load(buoy)
            assert p["buoy_id"] == buoy, f"{buoy} posterior.json buoy_id wrong"
            assert p["sensor_type"] == reference[buoy]["sensor_type"], f"{buoy} posterior.json sensor_type wrong"
            assert p["n_observations"] == reference[buoy]["n_observations"]

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

    def test_gate_partitions_fleet(self, included, gate):
        """Sanity: the §13 acceptance gate must accept some buoys and reject others."""
        n_acc = sum(gate.values())
        assert 0 < n_acc < len(included), (
            f"gate should partition the fleet; got {n_acc}/{len(included)} accepted"
        )

    def test_summary_accept_reject(self, included, gate, summary):
        """summary.json must list each buoy's accepted/rejected status matching the §13 gate."""
        acc = {b for b in included if gate[b]}
        rej = {b for b in included if not gate[b]}
        assert set(summary["accepted"]) == acc, "summary.json accepted list does not match the gate"
        assert set(summary["rejected"]) == rej, "summary.json rejected list does not match the gate"
        status = {b["buoy_id"]: b["status"] for b in summary["buoys"]}
        for buoy in included:
            assert status.get(buoy) == ("accepted" if gate[buoy] else "rejected"), f"{buoy} status wrong"

    def test_fleet_summary(self, included, reference, summary):
        """The fleet block must aggregate the per-buoy corrected RMSE and counts."""
        fleet = summary["fleet"]
        assert fleet["n_buoys"] == len(included)
        rmses = [reference[b]["calibration"]["corrected_rmse"] for b in included]
        assert fleet["mean_corrected_rmse"] == pytest.approx(float(np.mean(rmses)), rel=1e-3, abs=1e-9)

    def test_registry_accepted_only(self, included, gate, reference, registry):
        """registry.json must register exactly the accepted buoys with posterior-mean coefficients."""
        models = registry["models"]
        assert set(models) == {b for b in included if gate[b]}, (
            "registry must contain exactly the accepted buoys (no rejected buoys)"
        )
        for buoy, mdl in models.items():
            post = reference[buoy]["posterior"]
            assert mdl["offset"] == pytest.approx(post["offset"]["mean"], rel=1e-3, abs=1e-9), f"{buoy} offset coeff"
            assert mdl["drift"] == pytest.approx(post["drift"]["mean"], rel=1e-3, abs=1e-9), f"{buoy} drift coeff"
            assert mdl["drift_change"] == pytest.approx(post["drift_change"]["mean"], rel=1e-3, abs=1e-9), f"{buoy} drift_change coeff"
            assert mdl["changepoint_t_days"] == pytest.approx(reference[buoy]["changepoint_t_days"], abs=1e-6)

    def test_predict_matches_calibration(self, included, gate, reference):
        """Each accepted buoy's registered model, queried via `predict`, must return
        offset + drift*t + drift_change*hinge from the posterior means."""
        for buoy in included:
            if not gate[buoy]:
                continue
            post = reference[buoy]["posterior"]
            tc = reference[buoy]["changepoint_t_days"]
            for t in (10.0, 80.0, 150.0):
                hinge = max(0.0, t - tc)
                expected = post["offset"]["mean"] + post["drift"]["mean"] * t + post["drift_change"]["mean"] * hinge
                assert predict(buoy, t, hinge) == pytest.approx(expected, rel=1e-3, abs=1e-6), (
                    f"{buoy}: predict({t}, {hinge}) does not match the calibration"
                )
            # Pre-changepoint probe (hinge=0): catches conflating drift with drift_change.
            for t in (5.0, 40.0):
                expected0 = post["offset"]["mean"] + post["drift"]["mean"] * t
                assert predict(buoy, t, 0.0) == pytest.approx(expected0, rel=1e-3, abs=1e-6), (
                    f"{buoy}: pre-changepoint predict({t}, 0) is wrong"
                )

    def test_rejected_not_registered(self, included, gate, registry):
        """Rejected buoys must not be registered and must not resolve through predict."""
        for buoy in included:
            if gate[buoy]:
                continue
            assert buoy not in registry["models"], f"{buoy} was rejected and must not be registered"
            out = subprocess.run(
                [BINARY, "predict", "--buoy", buoy, "--t", "10.0", "--hinge", "0.0"],
                capture_output=True, text=True,
            )
            assert out.returncode != 0, f"{buoy} is rejected; predict must not resolve it"
