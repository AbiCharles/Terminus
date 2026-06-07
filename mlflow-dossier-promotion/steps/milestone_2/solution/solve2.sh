#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: write the training/logging pipeline as a source file and
# run it. It trains the candidate roster from /app/policy.json on /app/data.csv
# under the dossier's sampling protocol, then logs params, metrics, per-slice
# fairness statistics, a validation report, and the fitted model to the local
# MLflow store (sqlite backend at /app/mlflow.db, artifacts under /app/mlruns).
cat > /app/promote_train.py <<'PY'
"""Train the pre-registered candidate roster and log every candidate to MLflow."""
import json

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

with open("/app/policy.json") as fh:
    policy = json.load(fh)

target = policy["target_column"]
numeric = policy["feature_policy"]["numeric"]
categorical = policy["feature_policy"]["categorical"]
prohibited = policy["feature_policy"]["prohibited"]
protected = [s["column"] for s in policy["bias_slices"]]
artifact_path = policy["model_artifact_path"]

df = pd.read_csv("/app/data.csv")

# The canonical 70/15/15 partition is materialised in the dataset's `split`
# column; train on the train fold and evaluate on the test fold.
train_df = df[df["split"] == "train"]
test_df = df[df["split"] == "test"]


def demographic_parity_difference(predictions, group_series):
    rates = pd.Series(predictions, index=group_series.index).groupby(group_series).mean()
    return float(rates.max() - rates.min())


def build_estimator(candidate):
    if candidate["estimator"] == "LogisticRegression":
        return LogisticRegression(**candidate["params"])
    return GradientBoostingClassifier(**candidate["params"])


mlflow.set_tracking_uri("sqlite:////app/mlflow.db")
mlflow.set_experiment(policy["experiment_name"])

for candidate in policy["candidates"]:
    numeric_features = numeric + (prohibited if candidate["uses_prohibited_proxy"] else [])
    features = numeric_features + categorical
    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    pipeline = Pipeline([("preprocess", preprocessor), ("model", build_estimator(candidate))])
    pipeline.fit(train_df[features], train_df[target])

    proba = pipeline.predict_proba(test_df[features])[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(test_df[target], pred)),
        "f1_macro": float(f1_score(test_df[target], pred, average="macro")),
        "roc_auc": float(roc_auc_score(test_df[target], proba)),
    }
    bias = {col: demographic_parity_difference(pred, test_df[col]) for col in protected}

    with mlflow.start_run(run_name=candidate["name"]):
        mlflow.log_param("model_type", candidate["name"])
        mlflow.log_param("estimator", candidate["estimator"])
        mlflow.log_param("uses_prohibited_proxy", candidate["uses_prohibited_proxy"])
        for key, value in candidate["params"].items():
            mlflow.log_param(key, value)
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        for col, value in bias.items():
            mlflow.log_metric(f"bias_dpd_{col}", value)

        report = {
            "model_type": candidate["name"],
            "estimator": candidate["estimator"],
            "metrics": metrics,
            "bias_demographic_parity_difference": bias,
        }
        with open("/tmp/validation_report.json", "w") as fh:
            json.dump(report, fh, indent=2)
        mlflow.log_artifact("/tmp/validation_report.json")
        mlflow.sklearn.log_model(pipeline, name=artifact_path)
        print(f"logged {candidate['name']}: {metrics} bias={bias}")
PY

python3 /app/promote_train.py
