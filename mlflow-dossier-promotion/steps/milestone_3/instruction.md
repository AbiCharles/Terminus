Milestone 3 — promote the compliant champion.

Apply the dossier's gates to the candidate runs you logged in milestone 2. Disqualify any candidate that misses an acceptance threshold, then disqualify any remaining candidate that breaches a fairness ceiling for any protected attribute. From whatever survives, choose the champion as the one with the best value of the policy's ranking metric.

Register that champion's logged model — the scikit-learn model you logged for it in milestone 2 — as a new version of the policy's registered model name, and assign the policy's champion alias to that version. The registration must reference the logged model itself, not a bare run-artifact path: `mlflow.sklearn.load_model("models:/<registered_model_name>@<champion_alias>")` must succeed and return the fitted champion estimator. A registration whose alias cannot be loaded back does not count. The disqualified candidates stay as runs but must not be registered as the champion.
