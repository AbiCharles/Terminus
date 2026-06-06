#!/bin/bash
set -euo pipefail

# Milestone 1 oracle: encode the approval policy extracted from /app/dossier.md
# (governing sections §6–§13) into /app/policy.json. The values below are the
# binding criteria for the Edition 3 cycle; the superseded Edition 1/2 numbers
# that appear in the dossier's case studies and appendices are deliberately
# excluded.
python3 - <<'PY'
import json

policy = {
    "registered_model_name": "meridian_credit_default_classifier",
    "champion_alias": "champion",
    "experiment_name": "credit_default_promotion",
    "target_column": "default",
    "evaluation_split": "test",
    "model_artifact_path": "credit_default_model",
    "data_split": {
        "train": 0.70,
        "validation": 0.15,
        "test": 0.15,
        "stratify_on": "default",
        "random_state": 42,
    },
    "metric_thresholds": {
        "accuracy": 0.72,
        "f1_macro": 0.70,
        "roc_auc": 0.78,
    },
    "ranking_metric": "roc_auc",
    "feature_policy": {
        "numeric": [
            "income",
            "loan_amount",
            "dti_ratio",
            "credit_score",
            "employment_years",
            "num_open_accounts",
        ],
        "categorical": ["home_ownership", "loan_purpose"],
        "prohibited": ["region_risk_index"],
    },
    "bias_slices": [
        {"column": "age_group", "metric": "demographic_parity_difference", "max_disparity": 0.12},
        {"column": "gender", "metric": "demographic_parity_difference", "max_disparity": 0.10},
        {"column": "region", "metric": "demographic_parity_difference", "max_disparity": 0.15},
    ],
    "candidates": [
        {
            "name": "logreg_baseline",
            "estimator": "LogisticRegression",
            "uses_prohibited_proxy": False,
            "params": {"C": 1.0, "max_iter": 1000, "random_state": 42},
        },
        {
            "name": "gbm_audit",
            "estimator": "GradientBoostingClassifier",
            "uses_prohibited_proxy": True,
            "params": {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.1, "random_state": 42},
        },
        {
            "name": "gbm_compliant",
            "estimator": "GradientBoostingClassifier",
            "uses_prohibited_proxy": False,
            "params": {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.1, "random_state": 42},
        },
    ],
    "rollback_conditions": [
        {"id": "auc_floor", "metric": "roc_auc", "operator": "<", "threshold": 0.74},
        {"id": "drift_psi", "metric": "population_stability_index", "operator": ">", "threshold": 0.25},
        {"id": "approval_rate_floor", "metric": "weekly_approval_rate", "operator": "<", "threshold": 0.35},
    ],
}

with open("/app/policy.json", "w") as fh:
    json.dump(policy, fh, indent=2)
print("wrote /app/policy.json")
PY
