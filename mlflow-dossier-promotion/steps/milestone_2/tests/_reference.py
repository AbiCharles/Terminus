"""Independent reference implementation of the dossier protocol.

This module recomputes, from /app/data.csv alone, what every candidate's metrics
and fairness statistics must be and which candidate is the true compliant
champion. It mirrors the binding governing sections of /app/dossier.md and is the
verifier's answer key — it does NOT read the agent's /app/policy.json, so an agent
cannot weaken verification by tampering with the policy file. The agent has no
access to this module at solve time.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = "/app/data.csv"
TARGET = "default"
SEED = 42
NUMERIC = [
    "income",
    "loan_amount",
    "dti_ratio",
    "credit_score",
    "employment_years",
    "num_open_accounts",
]
CATEGORICAL = ["home_ownership", "loan_purpose"]
PROXY = "region_risk_index"
PROTECTED = ["age_group", "gender", "region"]

THRESHOLDS = {"accuracy": 0.72, "f1_macro": 0.70, "roc_auc": 0.78}
CAPS = {"age_group": 0.12, "gender": 0.10, "region": 0.15}
RANKING_METRIC = "roc_auc"

CANDIDATES = [
    {"name": "logreg_baseline", "kind": "logreg", "proxy": False},
    {"name": "gbm_audit", "kind": "gbm", "proxy": True},
    {"name": "gbm_compliant", "kind": "gbm", "proxy": False},
]
CANDIDATE_NAMES = {c["name"] for c in CANDIDATES}


def candidate_of_run(run, valid_names=CANDIDATE_NAMES):
    """Identify which roster candidate an MLflow run is, tolerant of how the agent
    recorded the model identity: a `model_type` param, a `model_type` tag, or the
    run name. Returns the candidate name, or None if the run is unrelated."""
    for value in (
        run.data.params.get("model_type"),
        run.data.tags.get("model_type"),
        run.data.tags.get("mlflow.runName"),
        getattr(run.info, "run_name", None),
    ):
        if value in valid_names:
            return value
    return None


def _estimator(kind):
    if kind == "logreg":
        return LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
    return GradientBoostingClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.1, random_state=SEED
    )


def _dpd(predictions, group_series):
    rates = pd.Series(predictions, index=group_series.index).groupby(group_series).mean()
    return float(rates.max() - rates.min())


def _split(df):
    # The canonical partition is materialised in the dataset's `split` column.
    return df[df["split"] == "train"], df[df["split"] == "test"]


def compute_reference():
    """Train every candidate and return {name: {metrics..., bias: {...}}}."""
    df = pd.read_csv(DATA_PATH)
    train_df, test_df = _split(df)
    results = {}
    for candidate in CANDIDATES:
        numeric_features = NUMERIC + ([PROXY] if candidate["proxy"] else [])
        features = numeric_features + CATEGORICAL
        preprocessor = ColumnTransformer(
            [
                ("num", StandardScaler(), numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ]
        )
        pipeline = Pipeline([("preprocess", preprocessor), ("model", _estimator(candidate["kind"]))])
        pipeline.fit(train_df[features], train_df[TARGET])
        proba = pipeline.predict_proba(test_df[features])[:, 1]
        pred = (proba >= 0.5).astype(int)
        results[candidate["name"]] = {
            "accuracy": float(accuracy_score(test_df[TARGET], pred)),
            "f1_macro": float(f1_score(test_df[TARGET], pred, average="macro")),
            "roc_auc": float(roc_auc_score(test_df[TARGET], proba)),
            "bias": {col: _dpd(pred, test_df[col]) for col in PROTECTED},
        }
    return results


def _passes(result):
    if any(result[m] < THRESHOLDS[m] for m in THRESHOLDS):
        return False
    return all(result["bias"][col] <= cap for col, cap in CAPS.items())


def true_champion(results=None):
    """Return the name of the unique compliant champion (highest ROC-AUC among survivors)."""
    if results is None:
        results = compute_reference()
    survivors = [name for name, result in results.items() if _passes(result)]
    return max(survivors, key=lambda name: results[name][RANKING_METRIC])
