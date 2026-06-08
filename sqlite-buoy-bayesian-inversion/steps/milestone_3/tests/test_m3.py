"""Tests for milestone 3 (Run Bayesian Inversion). Run alone with: pytest tests/test_m3.py

Verifies /app/artifacts/<buoy_id>/posterior.json reports the heteroscedastic,
(K+2)-parameter multi-change-point conjugate Gaussian posterior (offset, drift, and
one drift_change per changepoint) with means, standard deviations and 95% credible
intervals, the admitted observation count, the changepoints, and pre/post-correction
RMSE — all matched against an independent numpy recomputation that solves the full
(K+2)x(K+2) weighted normal-equations system from the database and binding priors
(_reference.py). Matching requires the weighted (1/std^2) GLS with all K hinge
regressors; an unweighted, two-parameter, or single-changepoint fit falls outside
tolerance.

The §13 acceptance gate (at least one drift_change credible interval excludes zero)
must partition the fleet into accepted/rejected, recorded in /app/artifacts/summary.json.
Accepted buoys' correction models must be registered in /app/artifacts/registry.json
(posterior means as coefficients) and be queryable through the program's `predict`
subcommand, which must return offset + drift*t + sum_k drift_change_k*max(0, t - cp_k);
rejected buoys must not be registered. A fleet summary aggregates the per-buoy corrected
RMSE over all calibrated buoys.
"""

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

import _reference

ARTIFACTS = Path("/app/artifacts")
BINARY = "/app/buoy_calibrate"


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
    """Per-buoy acceptance from the §13 gate (any drift_change CI excludes zero)."""
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


def predict(buoy, t):
    """Query the registered correction model through the program's predict subcommand."""
    out = subprocess.run(
        [BINARY, "predict", "--buoy", buoy, "--t", repr(float(t))],
        capture_output=True, text=True,
    )
    assert out.returncode == 0, f"predict failed for {buoy}: {out.stderr.strip()}"
    return float(out.stdout.strip())


def expected_correction(post, changepoints, t):
    val = post["offset"]["mean"] + post["drift"]["mean"] * t
    for dc, cp in zip(post["drift_changes"], changepoints):
        val += dc["mean"] * max(0.0, t - cp)
    return val


class TestMilestone3:
    """Milestone 3: heteroscedastic multi-change-point posterior per buoy."""

    def test_observation_count(self, included, reference):
        """Each posterior must report buoy_id, sensor_type and the admitted observation count."""
        for buoy in included:
            p = load(buoy)
            assert p["buoy_id"] == buoy, f"{buoy} posterior.json buoy_id wrong"
            assert p["sensor_type"] == reference[buoy]["sensor_type"], f"{buoy} posterior.json sensor_type wrong"
            assert p["n_observations"] == reference[buoy]["n_observations"]

    def test_changepoints(self, included, reference):
        """Each posterior must report all K changepoints in elapsed days, in order."""
        for buoy in included:
            got = load(buoy)["changepoints_t_days"]
            exp = reference[buoy]["changepoints_t_days"]
            assert len(got) == len(exp), f"{buoy} wrong number of changepoints"
            for g, e in zip(got, exp):
                assert g == pytest.approx(e, abs=1e-6), f"{buoy} changepoint mismatch"

    def test_posterior_offset_drift(self, included, reference):
        """Posterior mean/std of offset, drift and every drift_change must match the weighted GLS recompute."""
        for buoy in included:
            got = load(buoy)["posterior"]
            exp = reference[buoy]["posterior"]
            for key in ("offset", "drift"):
                assert got[key]["mean"] == pytest.approx(exp[key]["mean"], rel=2e-4, abs=1e-9), f"{buoy}.{key}.mean"
                assert got[key]["std"] == pytest.approx(exp[key]["std"], rel=2e-3, abs=1e-9), f"{buoy}.{key}.std"
            assert len(got["drift_changes"]) == len(exp["drift_changes"]), f"{buoy} wrong drift_changes count"
            for i, (g, e) in enumerate(zip(got["drift_changes"], exp["drift_changes"])):
                assert g["mean"] == pytest.approx(e["mean"], rel=2e-4, abs=1e-9), f"{buoy}.drift_changes[{i}].mean"
                assert g["std"] == pytest.approx(e["std"], rel=2e-3, abs=1e-9), f"{buoy}.drift_changes[{i}].std"

    def test_credible_intervals(self, included, reference):
        """The 95% credible intervals must match the recomputed bounds for every parameter."""
        for buoy in included:
            got = load(buoy)["credible_interval_95"]
            exp = reference[buoy]["credible_interval_95"]
            for key in ("offset", "drift"):
                assert got[key][0] == pytest.approx(exp[key][0], rel=2e-4, abs=1e-9), f"{buoy}.{key}.lo"
                assert got[key][1] == pytest.approx(exp[key][1], rel=2e-4, abs=1e-9), f"{buoy}.{key}.hi"
            for i, (g, e) in enumerate(zip(got["drift_changes"], exp["drift_changes"])):
                assert g[0] == pytest.approx(e[0], rel=2e-4, abs=1e-9), f"{buoy}.drift_changes[{i}].lo"
                assert g[1] == pytest.approx(e[1], rel=2e-4, abs=1e-9), f"{buoy}.drift_changes[{i}].hi"

    def test_calibration_metrics(self, included, reference):
        """Pre/post-correction RMSE must match, and correction must not worsen the residual."""
        for buoy in included:
            got = load(buoy)["calibration"]
            exp = reference[buoy]["calibration"]
            assert got["rmse_residual"] == pytest.approx(exp["rmse_residual"], rel=2e-4, abs=1e-9)
            assert got["corrected_rmse"] == pytest.approx(exp["corrected_rmse"], rel=2e-4, abs=1e-9)
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
        """The fleet block must aggregate corrected RMSE over ALL calibrated buoys."""
        fleet = summary["fleet"]
        assert fleet["n_buoys"] == len(included)
        rmses = [reference[b]["calibration"]["corrected_rmse"] for b in included]
        assert fleet["mean_corrected_rmse"] == pytest.approx(float(np.mean(rmses)), rel=2e-4, abs=1e-9)

    def test_registry_accepted_only(self, included, gate, reference, registry):
        """registry.json must register exactly the accepted buoys with posterior-mean coefficients."""
        models = registry["models"]
        assert set(models) == {b for b in included if gate[b]}, (
            "registry must contain exactly the accepted buoys (no rejected buoys)"
        )
        for buoy, mdl in models.items():
            post = reference[buoy]["posterior"]
            assert mdl["offset"] == pytest.approx(post["offset"]["mean"], rel=2e-4, abs=1e-9), f"{buoy} offset coeff"
            assert mdl["drift"] == pytest.approx(post["drift"]["mean"], rel=2e-4, abs=1e-9), f"{buoy} drift coeff"
            dcs = mdl["drift_changes"]
            assert len(dcs) == len(post["drift_changes"]), f"{buoy} wrong drift_changes count in registry"
            for i, (g, e) in enumerate(zip(dcs, post["drift_changes"])):
                assert g == pytest.approx(e["mean"], rel=2e-4, abs=1e-9), f"{buoy} drift_changes[{i}] coeff"
            for g, e in zip(mdl["changepoints_t_days"], reference[buoy]["changepoints_t_days"]):
                assert g == pytest.approx(e, abs=1e-6), f"{buoy} changepoint in registry"

    def test_predict_matches_calibration(self, included, gate, reference):
        """Each accepted buoy's registered model, queried via `predict`, must return
        offset + drift*t + sum_k drift_change_k*max(0, t - cp_k) from the posterior means."""
        for buoy in included:
            if not gate[buoy]:
                continue
            post = reference[buoy]["posterior"]
            cps = reference[buoy]["changepoints_t_days"]
            for t in (10.0, 60.0, 100.0, 160.0):
                expected = expected_correction(post, cps, t)
                assert predict(buoy, t) == pytest.approx(expected, rel=2e-4, abs=1e-6), (
                    f"{buoy}: predict({t}) does not match the calibration"
                )

    def test_rejected_not_registered(self, included, gate, registry):
        """Rejected buoys must not be registered and must not resolve through predict."""
        for buoy in included:
            if gate[buoy]:
                continue
            assert buoy not in registry["models"], f"{buoy} was rejected and must not be registered"
            out = subprocess.run(
                [BINARY, "predict", "--buoy", buoy, "--t", "10.0"],
                capture_output=True, text=True,
            )
            assert out.returncode != 0, f"{buoy} is rejected; predict must not resolve it"
