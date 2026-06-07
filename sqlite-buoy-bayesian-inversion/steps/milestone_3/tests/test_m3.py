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
        key = run.data.tags.get("buoy_id") or run.data.tags.get("mlflow.runName")
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
