#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: derive the approval policy by PARSING /app/dossier.md.
# It isolates the binding governing sections (§6–§13), strips bold markers, and
# extracts each value with a regex anchored on the Edition-3 phrasing so the
# superseded Edition 1/2 distractors (the 0.80 accuracy floor, the retired
# meridian_risk_model_v1 name, the `model` artifact path, the 80/10/10 split,
# etc.) are never matched. The result is written to /app/policy.json.
cat > /app/extract_policy.py <<'PY'
"""Extract the binding approval policy from the governance dossier."""
import json
import re

raw = open("/app/dossier.md", encoding="utf-8").read()

# Restrict to the binding governing sections; §14 onward is non-binding
# background and case-study material that carries the distractor values.
text = raw[raw.index("## §6"):raw.index("## §14")].replace("**", "")
text = re.sub(r"\s+", " ", text)


def find(pattern, *, cast=str):
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"extraction failed: {pattern}")
    return cast(match.group(1))


def backticked(sentence_pattern):
    seg = re.search(sentence_pattern, text)
    if not seg:
        raise SystemExit(f"extraction failed: {sentence_pattern}")
    return re.findall(r"`([a-z_]+)`", seg.group(1))


def candidate(pattern, names, casts):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"candidate extraction failed: {pattern}")
    estimator = m.group(1)
    params = {name: cast(m.group(i + 2)) for i, (name, cast) in enumerate(zip(names, casts))}
    return estimator, params


logreg_est, logreg_params = candidate(
    r"`logreg_baseline` . a `(LogisticRegression)` classifier.*?`C` equal to "
    r"([0-9]+\.[0-9]+), a maximum of ([0-9]+) solver iterations, and random state ([0-9]+)",
    ["C", "max_iter", "random_state"], [float, int, int],
)
audit_est, audit_params = candidate(
    r"`gbm_audit` . a `(GradientBoostingClassifier)` configured with ([0-9]+) estimators, "
    r"a maximum tree depth of ([0-9]+), a learning rate of ([0-9]+\.[0-9]+), and random state ([0-9]+)",
    ["n_estimators", "max_depth", "learning_rate", "random_state"], [int, int, float, int],
)
compliant_est, compliant_params = candidate(
    r"`gbm_compliant` . a `(GradientBoostingClassifier)` configured identically to `gbm_audit` "
    r"\(([0-9]+) estimators, maximum depth ([0-9]+), learning rate ([0-9]+\.[0-9]+), random state ([0-9]+)\)",
    ["n_estimators", "max_depth", "learning_rate", "random_state"], [int, int, float, int],
)

policy = {
    "registered_model_name": find(r"must be recorded is `([a-z_]+)`"),
    "champion_alias": find(r"production alias for the champion is the literal string `([a-z_]+)`"),
    "experiment_name": find(r"tracking experiment named `([a-z_]+)`"),
    "target_column": find(r"target column in the dataset is named `([a-z_]+)`"),
    "evaluation_split": find(r"fairness statistics are computed on the ([a-z]+) fold"),
    "model_artifact_path": find(r"must be logged under the artifact path `([a-z_]+)`"),
    "data_split": {
        "train": find(r"into ([0-9]+) percent training", cast=int) / 100,
        "validation": find(r"percent training, ([0-9]+) percent validation", cast=int) / 100,
        "test": find(r"percent validation, and ([0-9]+) percent test", cast=int) / 100,
        "stratify_on": find(r"stratified on the `([a-z_]+)` outcome"),
        "random_state": find(r"seeded with the integer random state ([0-9]+)", cast=int),
    },
    "metric_thresholds": {
        "accuracy": find(r"minimum acceptable accuracy is ([0-9]+\.[0-9]+)", cast=float),
        "f1_macro": find(r"minimum acceptable macro-averaged F1 score \(.*?\) is ([0-9]+\.[0-9]+)", cast=float),
        "roc_auc": find(r"minimum acceptable area under the ROC curve is ([0-9]+\.[0-9]+)", cast=float),
    },
    "ranking_metric": "roc_auc" if re.search(r"ROC-AUC is the ranking metric", text) else None,
    "feature_policy": {
        "numeric": backticked(r"approved numeric features are (.+?)\."),
        "categorical": backticked(r"approved categorical features are (.+?)\."),
        "prohibited": [find(r"`([a-z_]+)` is the sole entry on the prohibited-feature list")],
    },
    "bias_slices": [
        {"column": col, "metric": "demographic_parity_difference",
         "max_disparity": find(rf"ceiling for `{col}` is ([0-9]+\.[0-9]+)", cast=float)}
        for col in ("age_group", "gender", "region")
    ],
    "candidates": [
        {"name": "logreg_baseline", "estimator": logreg_est, "uses_prohibited_proxy": False,
         "params": logreg_params},
        {"name": "gbm_audit", "estimator": audit_est, "uses_prohibited_proxy": True,
         "params": audit_params},
        {"name": "gbm_compliant", "estimator": compliant_est, "uses_prohibited_proxy": False,
         "params": compliant_params},
    ],
    "rollback_conditions": [
        {"id": "auc_floor",
         "metric": find(r"`auc_floor`[^.]*?metric `(\w+)`"), "operator": "<",
         "threshold": find(r"`auc_floor`[^.]*?falls below ([0-9]+\.[0-9]+)", cast=float)},
        {"id": "drift_psi",
         "metric": find(r"`drift_psi`[^.]*?metric `(\w+)`"), "operator": ">",
         "threshold": find(r"`drift_psi`[^.]*?rises above ([0-9]+\.[0-9]+)", cast=float)},
        {"id": "approval_rate_floor",
         "metric": find(r"`approval_rate_floor`[^.]*?metric `(\w+)`"), "operator": "<",
         "threshold": find(r"`approval_rate_floor`[^.]*?falls below ([0-9]+\.[0-9]+)", cast=float)},
    ],
}

with open("/app/policy.json", "w") as fh:
    json.dump(policy, fh, indent=2)
print("wrote /app/policy.json from dossier extraction")
PY

python3 /app/extract_policy.py
