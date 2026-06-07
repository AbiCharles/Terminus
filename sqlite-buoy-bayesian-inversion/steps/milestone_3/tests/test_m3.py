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

import mlflow
import mlflow.sklearn
import numpy as np
import pytest
from mlflow.tracking import MlflowClient

import _reference

REGISTERED_MODEL = "buoy_drift_correction"
TRACKING_URI = "sqlite:////app/mlflow.db"
EXPERIMENT_NAME = "buoy-calibration"


@pytest.fixture(scope="module")
def gate(included):
    """Per-buoy acceptance from the §13 gate (drift_change CI excludes zero)."""
    return {b: _reference.accepted(b) for b in included}


@pytest.fixture(scope="module")
def runs_by_buoy():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    assert experiment is not None, f"MLflow experiment '{EXPERIMENT_NAME}' was not created"
    mapping = {}
    for run in client.search_runs([experiment.experiment_id]):
        key = run.data.tags.get("buoy_id")  # must be tagged with buoy_id (no run-name fallback)
        if key:
            mapping[key] = run
    return mapping

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

    def test_run_status_tags(self, included, gate, runs_by_buoy):
        """Each buoy's MLflow run must be tagged accepted/rejected per the gate."""
        for buoy in included:
            run = runs_by_buoy.get(buoy)
            assert run is not None, f"{buoy} has no MLflow run in '{EXPERIMENT_NAME}'"
            expected = "accepted" if gate[buoy] else "rejected"
            assert run.data.tags.get("status") == expected, (
                f"{buoy} run status tag should be {expected}"
            )

    def test_run_params_and_metrics(self, included, reference, runs_by_buoy):
        """Each buoy's run must be named after the buoy and log the required params and metrics
        (experiment 'buoy-calibration' is enforced by the runs_by_buoy fixture)."""
        for buoy in included:
            run = runs_by_buoy[buoy]
            assert run.info.run_name == buoy, f"{buoy} run must be named '{buoy}'"
            params = run.data.params
            assert params.get("sensor_type") == reference[buoy]["sensor_type"], f"{buoy} missing/incorrect sensor_type param"
            assert int(params["n_observations"]) == reference[buoy]["n_observations"], f"{buoy} n_observations param wrong"
            assert float(params["changepoint_t_days"]) == pytest.approx(
                reference[buoy]["changepoint_t_days"], abs=1e-6
            ), f"{buoy} changepoint_t_days param wrong"
            metrics = run.data.metrics
            post = reference[buoy]["posterior"]
            for p in PARAMS:
                assert metrics[f"{p}_mean"] == pytest.approx(post[p]["mean"], rel=1e-3, abs=1e-9), f"{buoy} {p}_mean metric"
                assert metrics[f"{p}_std"] == pytest.approx(post[p]["std"], rel=1e-2, abs=1e-9), f"{buoy} {p}_std metric"
            assert metrics["corrected_rmse"] == pytest.approx(
                reference[buoy]["calibration"]["corrected_rmse"], rel=1e-3, abs=1e-9
            ), f"{buoy} corrected_rmse metric"

    def test_accepted_models_registered_and_predict(self, included, gate, reference):
        """Accepted buoys must have their model registered under the buoy_id alias and, when
        loaded, predict offset+drift*t+drift_change*hinge; rejected buoys must NOT be registered."""
        mlflow.set_tracking_uri(TRACKING_URI)
        for buoy in included:
            uri = f"models:/{REGISTERED_MODEL}@{buoy}"
            if gate[buoy]:
                model = mlflow.sklearn.load_model(uri)
                post = reference[buoy]["posterior"]
                tc = reference[buoy]["changepoint_t_days"]
                t = np.array([10.0, 80.0, 150.0], dtype=np.float64)
                hinge = np.maximum(0.0, t - tc)
                pred = np.asarray(model.predict(np.column_stack([t, hinge])), dtype=np.float64)
                expected = post["offset"]["mean"] + post["drift"]["mean"] * t + post["drift_change"]["mean"] * hinge
                assert np.allclose(pred, expected, rtol=1e-3, atol=1e-6), (
                    f"{buoy}: registered model predictions do not match the calibration"
                )
                # Pre-changepoint probe (hinge=0): catches a model that conflates
                # drift with drift_change or ignores the hinge feature.
                t0 = np.array([5.0, 40.0], dtype=np.float64)
                pred0 = np.asarray(model.predict(np.column_stack([t0, np.zeros_like(t0)])), dtype=np.float64)
                expected0 = post["offset"]["mean"] + post["drift"]["mean"] * t0
                assert np.allclose(pred0, expected0, rtol=1e-3, atol=1e-6), (
                    f"{buoy}: pre-changepoint predictions (hinge=0) are wrong"
                )
            else:
                try:
                    mlflow.sklearn.load_model(uri)
                    raise AssertionError(f"{buoy} was rejected by the gate and must NOT be registered/aliased")
                except AssertionError:
                    raise
                except Exception:
                    pass  # expected: alias does not resolve for a rejected buoy

    def test_logged_model_entity_exists(self, included, gate, runs_by_buoy):
        """Accepted buoys must log the model via the MLflow 3.x logged-model API (a LoggedModel
        entity tied to the run), not a raw artifact — verified through search_logged_models."""
        client = MlflowClient()
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        logged_run_ids = {lm.source_run_id for lm in client.search_logged_models(experiment_ids=[experiment.experiment_id])}
        for buoy in included:
            if gate[buoy]:
                run_id = runs_by_buoy[buoy].info.run_id
                assert run_id in logged_run_ids, (
                    f"{buoy} (accepted) must log a model via mlflow.sklearn.log_model "
                    f"(no LoggedModel found for its run)"
                )

    def test_model_version_tag(self, included, gate):
        """Each accepted buoy's registered model VERSION must be tagged validation_status=accepted
        and be resolvable via its alias (MLflow 3.x registry API: get_model_version_by_alias)."""
        client = MlflowClient()
        for buoy in included:
            if gate[buoy]:
                mv = client.get_model_version_by_alias(REGISTERED_MODEL, buoy)
                assert mv.tags.get("validation_status") == "accepted", (
                    f"{buoy}: registered model version must be tagged validation_status=accepted"
                )

    def test_summary_accept_reject(self, included, gate):
        """summary.json must list the accepted and rejected buoys and n_accepted per the gate."""
        summary = json.loads((ARTIFACTS / "summary.json").read_text())
        exp_acc = sorted(b for b in included if gate[b])
        exp_rej = sorted(b for b in included if not gate[b])
        assert sorted(summary.get("accepted", [])) == exp_acc, "summary.accepted must list accepted buoys"
        assert sorted(summary.get("rejected", [])) == exp_rej, "summary.rejected must list rejected buoys"
        assert summary["fleet"]["n_accepted"] == len(exp_acc), "fleet.n_accepted must match the gate"

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
