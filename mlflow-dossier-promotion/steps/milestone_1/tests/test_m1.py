"""Tests for milestone 1 (Codify Dossier Rules). Run alone with: pytest tests/test_m1.py

These tests verify that /app/policy.json encodes the *binding* Edition 3 criteria
from the governing sections of /app/dossier.md, and that none of the superseded
Edition 1/2 distractor values (e.g. an 0.80 accuracy floor or the retired
`meridian_risk_model_v1` name) leaked into the policy.
"""

import json
import math
from pathlib import Path

import pytest

POLICY_PATH = Path("/app/policy.json")


@pytest.fixture(scope="module")
def policy():
    assert POLICY_PATH.exists(), "/app/policy.json does not exist — milestone 1 not completed"
    with POLICY_PATH.open() as fh:
        return json.load(fh)


class TestMilestone1:
    """Milestone 1: the approval policy extracted from the dossier into /app/policy.json."""

    def test_policy_is_valid_json_object(self, policy):
        """/app/policy.json must parse as a JSON object."""
        assert isinstance(policy, dict), "policy.json must be a JSON object"

    def test_registry_identity(self, policy):
        """Registered model name, champion alias, experiment, target and artifact path match §6/§7."""
        assert policy["registered_model_name"] == "meridian_credit_default_classifier"
        assert policy["champion_alias"] == "champion"
        assert policy["experiment_name"] == "credit_default_promotion"
        assert policy["target_column"] == "default"
        assert policy["model_artifact_path"] == "credit_default_model"
        assert policy["evaluation_split"] == "test"

    def test_does_not_use_superseded_identity(self, policy):
        """Retired Edition 1/2 identifiers must not be used (distractor rejection)."""
        assert policy["registered_model_name"] != "meridian_risk_model_v1"
        assert policy["model_artifact_path"] != "model"

    def test_data_split_protocol(self, policy):
        """Data split must be the stratified 70/15/15 protocol seeded with random state 42 (§7)."""
        split = policy["data_split"]
        assert math.isclose(split["train"], 0.70, abs_tol=1e-9)
        assert math.isclose(split["validation"], 0.15, abs_tol=1e-9)
        assert math.isclose(split["test"], 0.15, abs_tol=1e-9)
        assert split["stratify_on"] == "default"
        assert split["random_state"] == 42

    def test_metric_thresholds(self, policy):
        """Acceptance thresholds must be accuracy 0.72, macro-F1 0.70, ROC-AUC 0.78 (§10)."""
        thresholds = policy["metric_thresholds"]
        assert math.isclose(thresholds["accuracy"], 0.72, abs_tol=1e-9)
        assert math.isclose(thresholds["f1_macro"], 0.70, abs_tol=1e-9)
        assert math.isclose(thresholds["roc_auc"], 0.78, abs_tol=1e-9)

    def test_ranking_metric(self, policy):
        """The champion ranking metric must be ROC-AUC (§10)."""
        assert policy["ranking_metric"] == "roc_auc"

    def test_feature_policy(self, policy):
        """Approved numeric/categorical features and the prohibited proxy must match §9."""
        fp = policy["feature_policy"]
        approved_numeric = {
            "income",
            "loan_amount",
            "dti_ratio",
            "credit_score",
            "employment_years",
            "num_open_accounts",
        }
        assert set(fp["numeric"]) == approved_numeric
        assert set(fp["categorical"]) == {"home_ownership", "loan_purpose"}
        # The regional proxy must be prohibited, and no approved predictor may be
        # listed as prohibited. Listing the protected attributes here too is a
        # defensible reading of §9 ("never used as model inputs"), so it is allowed.
        prohibited = set(fp["prohibited"])
        approved = approved_numeric | {"home_ownership", "loan_purpose"}
        assert "region_risk_index" in prohibited, (
            "the regional proxy 'region_risk_index' must be on the prohibited list"
        )
        assert not (prohibited & approved), (
            f"approved predictors must not be prohibited: {prohibited & approved}"
        )

    def test_bias_ceilings(self, policy):
        """Fairness ceilings must be age_group 0.12, gender 0.10, region 0.15 (§11)."""
        ceilings = {s["column"]: s["max_disparity"] for s in policy["bias_slices"]}
        assert math.isclose(ceilings["age_group"], 0.12, abs_tol=1e-9)
        assert math.isclose(ceilings["gender"], 0.10, abs_tol=1e-9)
        assert math.isclose(ceilings["region"], 0.15, abs_tol=1e-9)
        for slice_spec in policy["bias_slices"]:
            assert slice_spec["metric"] == "demographic_parity_difference"

    def test_candidate_roster(self, policy):
        """The candidate roster must match §8: three named candidates with the stated configs."""
        candidates = {c["name"]: c for c in policy["candidates"]}
        assert set(candidates) == {"logreg_baseline", "gbm_audit", "gbm_compliant"}

        logreg = candidates["logreg_baseline"]
        assert logreg["estimator"].rsplit(".", 1)[-1] == "LogisticRegression"
        assert logreg["uses_prohibited_proxy"] is False
        assert logreg["params"]["C"] == 1.0
        assert logreg["params"]["max_iter"] == 1000
        assert logreg["params"]["random_state"] == 42

        for name in ("gbm_audit", "gbm_compliant"):
            gbm = candidates[name]
            assert gbm["estimator"].rsplit(".", 1)[-1] == "GradientBoostingClassifier"
            assert gbm["params"]["n_estimators"] == 200
            assert gbm["params"]["max_depth"] == 3
            assert math.isclose(gbm["params"]["learning_rate"], 0.1, abs_tol=1e-9)
            assert gbm["params"]["random_state"] == 42

        # Only the audit challenger uses the prohibited regional proxy.
        assert candidates["gbm_audit"]["uses_prohibited_proxy"] is True
        assert candidates["gbm_compliant"]["uses_prohibited_proxy"] is False

    def test_rollback_conditions(self, policy):
        """Rollback triggers must match §13: auc_floor<0.74, drift_psi>0.25, approval_rate_floor<0.35."""
        conditions = {c["id"]: c for c in policy["rollback_conditions"]}
        assert set(conditions) == {"auc_floor", "drift_psi", "approval_rate_floor"}
        assert conditions["auc_floor"]["operator"] == "<"
        assert math.isclose(conditions["auc_floor"]["threshold"], 0.74, abs_tol=1e-9)
        assert conditions["drift_psi"]["operator"] == ">"
        assert math.isclose(conditions["drift_psi"]["threshold"], 0.25, abs_tol=1e-9)
        assert conditions["approval_rate_floor"]["operator"] == "<"
        assert math.isclose(conditions["approval_rate_floor"]["threshold"], 0.35, abs_tol=1e-9)
