"""Parse the binding approval policy out of the governance dossier.

This is the extraction logic for milestone 1's oracle. It reads dossier.md,
isolates the governing sections (§6–§13), strips bold markers, and pulls each
value with a regex anchored on the Edition-3 phrasing so the superseded
Edition 1/2 distractors (0.80 floor, meridian_risk_model_v1, artifact path
`model`, 80/10/10 split, etc.) are never matched.
"""
import json
import re
import sys

DOSSIER = sys.argv[1] if len(sys.argv) > 1 else "/app/dossier.md"


def main():
    raw = open(DOSSIER, encoding="utf-8").read()

    # Restrict to the binding governing sections (§6 starts identity, §14 begins
    # the non-binding background/case-study material that carries distractors).
    start = raw.index("## §6")
    end = raw.index("## §14")
    text = raw[start:end].replace("**", "")
    text = re.sub(r"\s+", " ", text)  # collapse wrapped lines

    def find(pattern, *, cast=str, group=1):
        m = re.search(pattern, text)
        if not m:
            raise SystemExit(f"extraction failed for pattern: {pattern}")
        return cast(m.group(group))

    def backticked(sentence_pattern):
        seg = re.search(sentence_pattern, text)
        if not seg:
            raise SystemExit(f"extraction failed for list: {sentence_pattern}")
        return re.findall(r"`([a-z_]+)`", seg.group(1))

    policy = {
        "registered_model_name": find(r"must be recorded is `([a-z_]+)`"),
        "champion_alias": find(r"production alias for the champion is the literal string `([a-z_]+)`"),
        "experiment_name": find(r"tracking experiment named `([a-z_]+)`"),
        "target_column": find(r"target column in the dataset is named `([a-z_]+)`"),
        "evaluation_split": find(r"metrics and all fairness statistics are computed on the ([a-z]+) fold"),
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
            {"column": c, "metric": "demographic_parity_difference",
             "max_disparity": find(rf"ceiling for `{c}` is ([0-9]+\.[0-9]+)", cast=float)}
            for c in ("age_group", "gender", "region")
        ],
        "candidates": _candidates(text),
        "rollback_conditions": [
            {"id": "auc_floor", "metric": "roc_auc", "operator": "<",
             "threshold": find(r"`auc_floor`, fires when the monitored production ROC-AUC falls below ([0-9]+\.[0-9]+)", cast=float)},
            {"id": "drift_psi", "metric": "population_stability_index", "operator": ">",
             "threshold": find(r"`drift_psi`, fires when the population stability index .*? rises above ([0-9]+\.[0-9]+)", cast=float)},
            {"id": "approval_rate_floor", "metric": "weekly_approval_rate", "operator": "<",
             "threshold": find(r"`approval_rate_floor`, fires when the weekly approval rate falls below ([0-9]+\.[0-9]+)", cast=float)},
        ],
    }
    return policy, text


def _candidates(text):
    logreg = re.search(
        r"`logreg_baseline` . a `(LogisticRegression)` classifier.*?`C` equal to ([0-9]+\.[0-9]+), "
        r"a maximum of ([0-9]+) solver iterations, and random state ([0-9]+)",
        text,
    )
    audit = re.search(
        r"`gbm_audit` . a `(GradientBoostingClassifier)` configured with ([0-9]+) estimators, "
        r"a maximum tree depth of ([0-9]+), a learning rate of ([0-9]+\.[0-9]+), and random state ([0-9]+)",
        text,
    )
    compliant = re.search(
        r"`gbm_compliant` . a `(GradientBoostingClassifier)` configured identically to `gbm_audit` "
        r"\(([0-9]+) estimators, maximum depth ([0-9]+), learning rate ([0-9]+\.[0-9]+), random state ([0-9]+)\)",
        text,
    )
    if not (logreg and audit and compliant):
        raise SystemExit("candidate roster extraction failed")
    return [
        {"name": "logreg_baseline", "estimator": logreg.group(1), "uses_prohibited_proxy": False,
         "params": {"C": float(logreg.group(2)), "max_iter": int(logreg.group(3)),
                    "random_state": int(logreg.group(4))}},
        {"name": "gbm_audit", "estimator": audit.group(1), "uses_prohibited_proxy": True,
         "params": {"n_estimators": int(audit.group(2)), "max_depth": int(audit.group(3)),
                    "learning_rate": float(audit.group(4)), "random_state": int(audit.group(5))}},
        {"name": "gbm_compliant", "estimator": compliant.group(1), "uses_prohibited_proxy": False,
         "params": {"n_estimators": int(compliant.group(2)), "max_depth": int(compliant.group(3)),
                    "learning_rate": float(compliant.group(4)), "random_state": int(compliant.group(5))}},
    ]


if __name__ == "__main__":
    policy, _ = main()
    print(json.dumps(policy, indent=2))
