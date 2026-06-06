"""Generate the synthetic credit-risk dataset for the MLflow dossier task.

Design goals (empirically tuned in dev, see explore.py):
  * Strong NONLINEAR signal (interactions, thresholds, XOR) so tree models
    clearly beat LogisticRegression on ROC-AUC -> logreg fails the metric gate.
  * A `region` protected attribute with a real base-rate gap that is NOT
    recoverable from the approved feature set, plus a `region_risk_index`
    PROXY column that encodes region. A model that uses the proxy reproduces
    the regional gap in its predictions -> high demographic-parity disparity
    (fails the region bias cap). A model on approved features only stays under
    the cap -> compliant champion.
  * age_group / gender carry negligible signal so their disparities stay under
    their caps for every candidate (they never decide the outcome).
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(20240517)
N = 9000


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# ---- protected attributes ----
gender = RNG.choice(["F", "M"], size=N, p=[0.49, 0.51])
age_group = RNG.choice(["18-25", "26-40", "41-60", "60+"], size=N, p=[0.18, 0.4, 0.3, 0.12])
region = RNG.choice(["north", "south", "east", "west"], size=N, p=[0.28, 0.27, 0.25, 0.2])

# region base-rate effect (orthogonal to approved features) -> creates a real gap.
# Wide gap so the proxy model's regional disparity clears the cap while a model
# blind to region stays well under it.
region_logit = {"north": -1.0, "south": -0.2, "east": 0.6, "west": 1.35}
region_eff = np.array([region_logit[r] for r in region])
# proxy column: encodes region with noise (continuous risk index ~0..1)
region_center = {"north": 0.2, "south": 0.4, "east": 0.6, "west": 0.82}
region_risk_index = np.clip(
    np.array([region_center[r] for r in region]) + RNG.normal(0, 0.06, N), 0, 1
).round(4)

# ---- approved numeric features (independent of region) ----
income = np.clip(np.exp(RNG.normal(10.85, 0.45, N)), 18000, 250000).round(0)
loan_amount = np.clip(income * RNG.uniform(0.08, 0.65, N) + RNG.normal(0, 1500, N), 1000, None).round(0)
dti_ratio = np.clip(loan_amount / income * RNG.uniform(0.5, 1.4, N), 0.03, 0.75).round(4)
credit_score = np.clip(RNG.normal(685, 62, N), 480, 840).astype(int)
employment_years = np.clip(RNG.gamma(2.2, 3.2, N), 0, 41).round(1)
num_open_accounts = np.clip(RNG.poisson(4.0, N) + 1, 1, 24).astype(int)
home_ownership = RNG.choice(["RENT", "MORTGAGE", "OWN"], size=N, p=[0.42, 0.43, 0.15])
loan_purpose = RNG.choice(
    ["debt_consolidation", "home_improvement", "major_purchase", "medical", "small_business"],
    size=N, p=[0.4, 0.22, 0.18, 0.12, 0.08],
)

# ---- nonlinear true risk (logit) ----
cs = (credit_score - 685) / 62.0
dti_c = (dti_ratio - 0.3) / 0.12
inc_c = (np.log(income) - 10.85) / 0.45
emp_c = (employment_years - 7.0) / 5.0

rent = (home_ownership == "RENT").astype(float)
debtcon = (loan_purpose == "debt_consolidation").astype(float)

# Binarized conditions used to build XOR / high-order interactions. Each is
# (near) balanced, so its MAIN effect is ~0 -> a linear model on the raw
# features cannot capture these terms, while trees can. The signal is
# deliberately dominated by these interactions so GBM clearly beats LogReg.
t1 = (credit_score < 650).astype(float)
t2 = (dti_ratio > 0.30).astype(float)
t3 = (income < 45000).astype(float)
t4 = (employment_years < 4).astype(float)
t5 = (num_open_accounts > 6).astype(float)
cat_xor = ((rent + debtcon) == 1).astype(float)  # RENT xor debt_consolidation

age_logit = {"18-25": 0.1, "26-40": 0.0, "41-60": -0.03, "60+": 0.06}
age_eff = np.array([age_logit[a] for a in age_group])

z = (
    -4.05
    # modest linear main effects
    - 0.45 * cs
    + 0.35 * dti_c
    - 0.2 * inc_c
    - 0.15 * emp_c
    # dominant interaction / XOR signal (zero main effect -> linear can't fit)
    + 2.3 * ((t1 + t2) == 1).astype(float)        # credit_low xor high_dti
    + 2.1 * ((t3 + t4) == 1).astype(float)        # low_income xor short_employ
    + 1.9 * cat_xor                                # RENT xor debt_consolidation
    + 1.7 * (t1 * t2 * t5)                         # triple interaction
    - 1.5 * (t1 * t3 * (1 - t2))                   # protective high-order pocket
    + region_eff
    + age_eff
    + RNG.normal(0, 0.3, N)
)
p_default = sigmoid(z)
default = RNG.binomial(1, p_default)

df = pd.DataFrame(
    {
        "income": income.astype(int),
        "loan_amount": loan_amount.astype(int),
        "dti_ratio": dti_ratio,
        "credit_score": credit_score,
        "employment_years": employment_years,
        "num_open_accounts": num_open_accounts,
        "home_ownership": home_ownership,
        "loan_purpose": loan_purpose,
        "region_risk_index": region_risk_index,  # PROHIBITED proxy
        "age_group": age_group,
        "gender": gender,
        "region": region,
        "default": default.astype(int),
    }
)

if __name__ == "__main__":
    df.to_csv("data.csv", index=False)
    print("rows", len(df), "default_rate", round(df.default.mean(), 3))
    print("by region:\n", df.groupby("region").default.mean().round(3))
    print("by gender:\n", df.groupby("gender").default.mean().round(3))
    print("by age:\n", df.groupby("age_group").default.mean().round(3))
