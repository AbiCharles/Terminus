#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: write the promotion logic as a source file and run it. It
# reads the logged candidate runs, applies the §10 acceptance thresholds and the
# §11 fairness ceilings, selects the surviving candidate with the highest
# ROC-AUC as champion, registers it under the dossier's registered model name,
# and assigns the champion alias.
cat > /app/promote_register.py <<'PY'
"""Apply the dossier gates to the logged runs and promote the compliant champion."""
import json

import mlflow
from mlflow.tracking import MlflowClient

with open("/app/policy.json") as fh:
    policy = json.load(fh)

thresholds = policy["metric_thresholds"]
caps = {s["column"]: s["max_disparity"] for s in policy["bias_slices"]}
ranking_metric = policy["ranking_metric"]
registered_name = policy["registered_model_name"]
alias = policy["champion_alias"]
artifact_path = policy["model_artifact_path"]

mlflow.set_tracking_uri("sqlite:////app/mlflow.db")
client = MlflowClient()

experiment = client.get_experiment_by_name(policy["experiment_name"])
runs = client.search_runs([experiment.experiment_id])


def passes_metrics(metrics):
    return (
        metrics["accuracy"] >= thresholds["accuracy"]
        and metrics["f1_macro"] >= thresholds["f1_macro"]
        and metrics["roc_auc"] >= thresholds["roc_auc"]
    )


def passes_fairness(metrics):
    return all(metrics[f"bias_dpd_{col}"] <= cap for col, cap in caps.items())


eligible = [
    run
    for run in runs
    if passes_metrics(run.data.metrics) and passes_fairness(run.data.metrics)
]
if not eligible:
    raise SystemExit("no compliant candidate; nothing to promote")

champion = max(eligible, key=lambda run: run.data.metrics[ranking_metric])
print(
    "champion:",
    champion.data.params["model_type"],
    "roc_auc=",
    champion.data.metrics["roc_auc"],
)

try:
    client.create_registered_model(registered_name)
except mlflow.exceptions.MlflowException:
    pass

source_uri = f"runs:/{champion.info.run_id}/{artifact_path}"
version = mlflow.register_model(source_uri, registered_name)
client.set_registered_model_alias(registered_name, alias, version.version)
print(f"registered {registered_name} v{version.version} with alias '{alias}'")
PY

python3 /app/promote_register.py
