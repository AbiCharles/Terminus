"""Tests for milestone 3 (Promote Registry Champion). Run alone with: pytest tests/test_m3.py

These tests verify that the MLflow Model Registry contains the registered model
with the champion alias pointing at the SINGLE compliant champion. The true
champion is recomputed independently (see _reference.py) from the dataset and the
dossier gates, so promoting the wrong model — for example the higher-AUC proxy
challenger that breaches the regional fairness ceiling — is rejected.
"""

from pathlib import Path

import mlflow
import pytest
from mlflow.tracking import MlflowClient

import _reference

TRACKING_URI = "sqlite:////app/mlflow.db"
EXPERIMENT = "credit_default_promotion"
REGISTERED_NAME = "meridian_credit_default_classifier"
ALIAS = "champion"
ARTIFACT_PATH = "credit_default_model"
DISQUALIFIED = {"gbm_audit", "logreg_baseline"}


@pytest.fixture(scope="module")
def client():
    mlflow.set_tracking_uri(TRACKING_URI)
    return MlflowClient()


@pytest.fixture(scope="module")
def champion_version(client):
    return client.get_model_version_by_alias(REGISTERED_NAME, ALIAS)


@pytest.fixture(scope="module")
def champion_model_type(client, champion_version):
    run = client.get_run(champion_version.run_id)
    return _reference.candidate_of_run(run, _reference.CANDIDATE_NAMES)


@pytest.fixture(scope="module")
def expected_champion():
    return _reference.true_champion()


class TestMilestone3:
    """Milestone 3: the compliant champion is registered with the champion alias."""

    def test_prior_artifacts_persist(self):
        """Milestone 1/2 artifacts (policy.json, mlflow.db) must still exist (state persists)."""
        assert Path("/app/policy.json").exists(), "policy.json missing — was milestone 1 completed?"
        assert Path("/app/mlflow.db").exists(), "mlflow.db missing — was milestone 2 completed?"

    def test_registered_model_exists(self, client):
        """A registered model with the dossier's registered name must exist."""
        model = client.get_registered_model(REGISTERED_NAME)
        assert model is not None and model.name == REGISTERED_NAME

    def test_champion_alias_assigned(self, champion_version):
        """The 'champion' alias must resolve to a concrete registered version."""
        assert champion_version is not None
        assert champion_version.version is not None

    def test_champion_is_the_compliant_candidate(self, champion_model_type, expected_champion):
        """The aliased champion must be the independently recomputed compliant champion (gbm_compliant)."""
        assert champion_model_type == expected_champion, (
            f"champion alias points to '{champion_model_type}', expected '{expected_champion}'"
        )

    def test_disqualified_candidates_not_promoted(self, champion_model_type):
        """The champion must not be a candidate that fails a metric or fairness gate."""
        assert champion_model_type not in DISQUALIFIED, (
            f"a disqualified candidate ('{champion_model_type}') was promoted"
        )

    def test_champion_artifact_naming(self, client, champion_version):
        """The promoted version's model artifact must use the credit_default_model name (§6).

        Tolerant of how the champion was registered: from a runs:/<run>/credit_default_model
        URI (source ends with the artifact name) or from an MLflow 3.x logged model
        (source ends with a model id whose logged-model name is credit_default_model).
        """
        source = champion_version.source.rstrip("/")
        last = source.split("/")[-1]
        if last == ARTIFACT_PATH or ARTIFACT_PATH in source:
            return
        try:
            logged_model = client.get_logged_model(last)
        except Exception as exc:  # pragma: no cover - defensive
            raise AssertionError(
                f"champion source '{champion_version.source}' does not reference "
                f"'{ARTIFACT_PATH}' and is not a resolvable logged model: {exc}"
            )
        assert logged_model.name == ARTIFACT_PATH, (
            f"champion logged-model name '{logged_model.name}' is not '{ARTIFACT_PATH}'"
        )

    def test_champion_model_loads_and_predicts(self):
        """The promoted champion must load from the registry and produce predictions (real fitted model)."""
        import pandas as pd

        features = _reference.NUMERIC + _reference.CATEGORICAL
        model = mlflow.sklearn.load_model(f"models:/{REGISTERED_NAME}@{ALIAS}")
        sample = pd.read_csv("/app/data.csv")[features].head(20)
        predictions = model.predict(sample)
        assert len(predictions) == 20
        assert set(pd.unique(predictions)).issubset({0, 1})

    def test_gates_were_computed_for_all_candidates(self, client):
        """The promotion must follow from real gate evaluation: every candidate run
        must carry the acceptance/ranking metrics, so the champion cannot be chosen by
        deducing the answer from the dossier without computing the gates."""
        experiment = client.get_experiment_by_name(EXPERIMENT)
        assert experiment is not None, f"experiment '{EXPERIMENT}' missing"
        metrics_by_candidate = {}
        for run in client.search_runs([experiment.experiment_id]):
            name = _reference.candidate_of_run(run, _reference.CANDIDATE_NAMES)
            if name:
                metrics_by_candidate.setdefault(name, set()).update(run.data.metrics)
        assert _reference.CANDIDATE_NAMES.issubset(metrics_by_candidate), (
            f"missing candidate runs: {_reference.CANDIDATE_NAMES - set(metrics_by_candidate)}"
        )
        for name in _reference.CANDIDATE_NAMES:
            have = metrics_by_candidate[name]
            assert {"accuracy", "roc_auc"}.issubset(have), (
                f"{name} run is missing gate metrics (accuracy/roc_auc); gates not computed"
            )
