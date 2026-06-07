#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: train the multinomial discrete-time competing-risks hazard
# model on the train person-period rows using the exact design matrix and
# hyperparameters from /app/spec.md §4, then serialize it with joblib.
cat > /app/train_model.py <<'PY'
"""Fit the 3-class multinomial discrete-time hazard model and serialize it."""
import os

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

FEATURES = ["age", "log_biomarker", "treatment", "stage_II", "stage_III", "sex_M", "period"]


def design(df):
    return pd.DataFrame({
        "age": df["age"].to_numpy(float),
        "log_biomarker": np.log(df["biomarker"].to_numpy(float)),
        "treatment": df["treatment"].to_numpy(float),
        "stage_II": (df["stage"] == "II").astype(float),
        "stage_III": (df["stage"] == "III").astype(float),
        "sex_M": (df["sex"] == "M").astype(float),
        "period": df["period"].to_numpy(float),
    })[FEATURES]


con = duckdb.connect("/app/survival.duckdb")
train = con.execute("SELECT * FROM person_period WHERE split = 'train'").df()
con.close()

model = LogisticRegression(C=1.0, max_iter=5000, solver="lbfgs", tol=1e-8, random_state=42)
model.fit(design(train), train["period_outcome"].to_numpy(int))

os.makedirs("/app/artifacts", exist_ok=True)
joblib.dump(model, "/app/artifacts/survival_model.joblib")
print("trained multinomial hazard model; classes", list(model.classes_))
PY

python3 /app/train_model.py
