"""Tests for milestone 2 (Log Candidate Models). Run alone with: pytest tests/test_m2.py

These tests open the agent's MLflow tracking store and verify that every
candidate in the roster was logged with the required params, metrics, per-slice
fairness statistics, a validation report, and a fitted model artifact. The logged
metrics are checked against an INDEPENDENT retrain (see _reference.py) so that
fabricated or mis-computed metrics are rejected.
"""

from pathlib import Path

import mlflow
import pytest
from mlflow.tracking import MlflowClient

import _reference

TRACKING_URI = "sqlite:////app/mlflow.db"
EXPERIMENT = "credit_default_promotion"
EXPECTED_CANDIDATES = {"logreg_baseline", "gbm_audit", "gbm_compliant"}
# Tolerance for matching logged metrics against an independent retrain. Tight
# enough to catch fabricated/sloppy results (e.g. skipping the specified feature
# scaling shifts metrics by >0.015), loose enough to absorb benign solver-level
# variance from a faithful reimplementation.
METRIC_TOLERANCE = 1e-2


@pytest.fixture(scope="module")
def runs_by_model():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    experiment = client.get_experiment_by_name(EXPERIMENT)
    assert experiment is not None, f"MLflow experiment '{EXPERIMENT}' was not created"
    runs = client.search_runs([experiment.experiment_id])
    mapping = {}
    for run in runs:
        name = _reference.candidate_of_run(run, EXPECTED_CANDIDATES)
        if name:
            mapping[name] = run
    return mapping


@pytest.fixture(scope="module")
def reference():
    return _reference.compute_reference()


class TestMilestone2:
    """Milestone 2: candidate models trained and logged to the local MLflow store."""

    def test_policy_artifact_persists(self):
        """The /app/policy.json file from milestone 1 must still exist (state persists)."""
        assert Path("/app/policy.json").exists(), "policy.json missing — was milestone 1 completed?"

    def test_tracking_store_exists(self):
        """The sqlite-backed MLflow tracking store must exist at /app/mlflow.db."""
        assert Path("/app/mlflow.db").exists(), "/app/mlflow.db tracking store does not exist"

    def test_all_candidates_logged(self, runs_by_model):
        """Each of the three roster candidates must have its own MLflow run."""
        assert EXPECTED_CANDIDATES.issubset(set(runs_by_model)), (
            f"missing candidate runs: {EXPECTED_CANDIDATES - set(runs_by_model)}"
        )

    def test_required_params_logged(self, runs_by_model):
        """Each candidate run must log the estimator family and its random_state param."""
        for name in EXPECTED_CANDIDATES:
            params = runs_by_model[name].data.params
            assert "estimator" in params, f"{name} missing 'estimator' param"
            assert params.get("random_state") == "42", f"{name} must log random_state=42"

    def test_required_metrics_logged(self, runs_by_model):
        """Each candidate run must log accuracy, f1_macro, roc_auc and a dpd metric per protected slice."""
        for name in EXPECTED_CANDIDATES:
            metrics = runs_by_model[name].data.metrics
            for key in ("accuracy", "f1_macro", "roc_auc"):
                assert key in metrics, f"{name} missing metric '{key}'"
            for col in ("age_group", "gender", "region"):
                assert f"bias_dpd_{col}" in metrics, f"{name} missing fairness metric for {col}"

    def test_validation_report_artifact_logged(self, runs_by_model):
        """Each run must log a validation_report.json artifact (at any artifact path)."""
        client = MlflowClient()

        def walk_artifacts(run_id, path=""):
            for art in client.list_artifacts(run_id, path):
                if art.is_dir:
                    yield from walk_artifacts(run_id, art.path)
                else:
                    yield art.path

        for name in EXPECTED_CANDIDATES:
            run_id = runs_by_model[name].info.run_id
            basenames = {p.rsplit("/", 1)[-1] for p in walk_artifacts(run_id)}
            assert "validation_report.json" in basenames, (
                f"{name} missing validation_report.json artifact"
            )

    def test_model_logged_per_run(self, runs_by_model):
        """Each run must log a fitted model under the name credit_default_model (MLflow logged model)."""
        client = MlflowClient()
        experiment = client.get_experiment_by_name(EXPERIMENT)
        logged_by_run = {}
        for logged_model in client.search_logged_models(experiment_ids=[experiment.experiment_id]):
            logged_by_run.setdefault(logged_model.source_run_id, set()).add(logged_model.name)
        for name in EXPECTED_CANDIDATES:
            run_id = runs_by_model[name].info.run_id
            assert "credit_default_model" in logged_by_run.get(run_id, set()), (
                f"{name} did not log a model named 'credit_default_model'"
            )

    def test_logged_metrics_match_independent_retrain(self, runs_by_model, reference):
        """Logged metrics must match an independent retrain within tolerance (anti-fabrication)."""
        for name in EXPECTED_CANDIDATES:
            metrics = runs_by_model[name].data.metrics
            expected = reference[name]
            for key in ("accuracy", "f1_macro", "roc_auc"):
                assert abs(metrics[key] - expected[key]) <= METRIC_TOLERANCE, (
                    f"{name} {key}={metrics[key]:.4f} differs from reference {expected[key]:.4f}"
                )
            for col in ("age_group", "gender", "region"):
                assert abs(metrics[f"bias_dpd_{col}"] - expected["bias"][col]) <= METRIC_TOLERANCE, (
                    f"{name} bias_dpd_{col} differs from reference"
                )
