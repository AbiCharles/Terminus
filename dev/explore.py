"""Train the fixed candidate roster and print metrics + bias disparities.

Used in dev to pick threshold/disparity numbers that yield:
  logreg_baseline  -> fails a metric gate
  gbm_audit        -> passes metrics, fails region bias cap (uses proxy)
  gbm_compliant    -> passes everything (champion)
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "default"
APPROVED_NUM = ["income", "loan_amount", "dti_ratio", "credit_score", "employment_years", "num_open_accounts"]
APPROVED_CAT = ["home_ownership", "loan_purpose"]
PROXY = "region_risk_index"
PROTECTED = ["age_group", "gender", "region"]
SEED = 42


def make_preprocessor(num_features, cat_features):
    return ColumnTransformer(
        [
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
        ]
    )


def split(df):
    train, tmp = train_test_split(df, test_size=0.30, random_state=SEED, stratify=df[TARGET])
    val, test = train_test_split(tmp, test_size=0.50, random_state=SEED, stratify=tmp[TARGET])
    return train, val, test


def dpd(pred, slice_series):
    """Demographic-parity difference: max-min positive-prediction rate across groups."""
    rates = pd.Series(pred).groupby(slice_series.reset_index(drop=True)).mean()
    return float(rates.max() - rates.min())


def evaluate(name, estimator, num_features, cat_features, df):
    train, val, test = split(df)
    feats = num_features + cat_features
    pipe = Pipeline([("pre", make_preprocessor(num_features, cat_features)), ("clf", estimator)])
    pipe.fit(train[feats], train[TARGET])
    proba = pipe.predict_proba(test[feats])[:, 1]
    pred = (proba >= 0.5).astype(int)
    acc = accuracy_score(test[TARGET], pred)
    f1m = f1_score(test[TARGET], pred, average="macro")
    auc = roc_auc_score(test[TARGET], proba)
    bias = {col: round(dpd(pred, test[col]), 4) for col in PROTECTED}
    print(f"\n== {name} ==")
    print(f"  acc={acc:.4f}  f1_macro={f1m:.4f}  roc_auc={auc:.4f}")
    print(f"  bias(dpd): {bias}")
    return acc, f1m, auc, bias


def main():
    df = pd.read_csv("data.csv")
    evaluate(
        "logreg_baseline",
        LogisticRegression(C=1.0, max_iter=1000, random_state=SEED),
        APPROVED_NUM, APPROVED_CAT, df,
    )
    evaluate(
        "gbm_audit (proxy)",
        GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=SEED),
        APPROVED_NUM + [PROXY], APPROVED_CAT, df,
    )
    evaluate(
        "gbm_compliant",
        GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=SEED),
        APPROVED_NUM, APPROVED_CAT, df,
    )


if __name__ == "__main__":
    main()
