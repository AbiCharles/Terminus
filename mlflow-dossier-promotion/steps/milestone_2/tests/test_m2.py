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
METRIC_TOLERANCE = 2e-2


@pytest.fixture(scope="module")
def runs_by_model():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    experiment = client.get_experiment_by_name(EXPERIMENT)
    assert experiment is not None, f"MLflow experiment '{EXPERIMENT}' was not created"
    # Newest-first so the agent's most recent run for each candidate wins over any
    # stale exploratory runs left earlier in the shared tracking store. Among the
    # runs that identify as a candidate, prefer the most recent one that logs
    # model_type as a param (the spec-compliant run), falling back to the most
    # recent run otherwise identified as that candidate.
    runs = client.search_runs(
        [experiment.experiment_id], order_by=["attributes.start_time DESC"]
    )
    by_any = {}
    by_param = {}
    for run in runs:
        name = _reference.candidate_of_run(run, EXPECTED_CANDIDATES)
        if not name:
            continue
        by_any.setdefault(name, run)
        if run.data.params.get("model_type") == name:
            by_param.setdefault(name, run)
    return {**by_any, **by_param}


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
        """Each run must log model_type, estimator, random_state and every estimator
        hyperparameter as a flat, exact-named MLflow param (the instruction forbids
        prefixing or nesting), so prefixed names like clf__C or hp_random_state fail."""
        banned_prefixes = ("hp_", "param_", "params_", "est__", "estimator__", "model__", "clf__", "classifier__")
        for name in EXPECTED_CANDIDATES:
            params = runs_by_model[name].data.params
            # model_type must be an MLflow param (not merely a tag or the run name).
            assert params.get("model_type") == name, (
                f"{name} must log model_type={name} as an MLflow param (found params: {sorted(params)})"
            )
            assert "estimator" in params, f"{name} did not log an 'estimator' param"
            assert params.get("random_state") == "42", f"{name} must log random_state=42 as a param"
            if name == "logreg_baseline":
                assert params.get("C") == "1.0", f"{name} must log C=1.0 as a param"
                assert params.get("max_iter") == "1000", f"{name} must log max_iter=1000 as a param"
            else:
                assert params.get("n_estimators") == "200", f"{name} must log n_estimators=200 as a param"
                assert params.get("max_depth") == "3", f"{name} must log max_depth=3 as a param"
                assert params.get("learning_rate") == "0.1", f"{name} must log learning_rate=0.1 as a param"
            # No prefixed/nested hyperparameter names (e.g. sklearn Pipeline get_params()).
            for key in params:
                assert not any(key.startswith(p) for p in banned_prefixes), (
                    f"{name} param '{key}' is prefixed; the instruction requires exact "
                    f"scikit-learn names without prefixing or nesting"
                )

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
            assert any(b.startswith("validation_report") and b.endswith(".json") for b in basenames), (
                f"{name} missing a validation_report json artifact (found: {sorted(basenames)})"
            )

    def test_model_logged_per_run(self, runs_by_model):
        """Each run must log a fitted model at the credit_default_model path (either MLflow logging API)."""
        import mlflow.sklearn

        client = MlflowClient()
        experiment = client.get_experiment_by_name(EXPERIMENT)

        def model_logged(run_id):
            # 1) Standard runs:/ URI — works for the artifact_path= API and resolves
            #    for the MLflow 3.x name= API once the model is registered/logged.
            try:
                model = mlflow.sklearn.load_model(f"runs:/{run_id}/credit_default_model")
                if hasattr(model, "predict"):
                    return True
            except Exception:
                pass
            # 2) MLflow 3.x logged-model named credit_default_model for this run.
            try:
                for lm in client.search_logged_models(experiment_ids=[experiment.experiment_id]):
                    if lm.source_run_id == run_id and lm.name == "credit_default_model":
                        return True
            except Exception:
                pass
            # 3) A run-artifact directory named credit_default_model holding an MLmodel.
            try:
                for art in client.list_artifacts(run_id):
                    if art.is_dir and art.path.rsplit("/", 1)[-1] == "credit_default_model":
                        if any(a.path.endswith("MLmodel") for a in client.list_artifacts(run_id, art.path)):
                            return True
            except Exception:
                pass
            return False

        for name in EXPECTED_CANDIDATES:
            run_id = runs_by_model[name].info.run_id
            assert model_logged(run_id), (
                f"{name} did not log a fitted model at 'credit_default_model' "
                f"(runs:/{run_id}/credit_default_model)"
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
