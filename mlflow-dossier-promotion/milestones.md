# Milestones — MLflow Model Registry Promotion from Long Evaluation Dossiers

This task is completed in three sequential milestones in a shared `/app` container;
state persists between milestones.

## Milestone 1 — Codify Dossier Rules
Read the 50k+ token governance dossier at `/app/dossier.md` and extract its binding
approval policy into `/app/policy.json`: the registry identifiers and artifact path,
the stratified data-split protocol, the performance acceptance thresholds and ranking
metric, the approved/prohibited features, the per-attribute fairness ceilings, the full
candidate roster with hyperparameters, and the post-promotion rollback triggers. The
dossier quotes superseded values from earlier editions as distractors; only the current
edition's governing sections are binding.

## Milestone 2 — Log Candidate Models
Train every candidate in the roster on `/app/data.csv` under the dossier's sampling
protocol and log each as its own MLflow run (sqlite backend at `/app/mlflow.db`,
artifacts under `/app/mlruns`): params, the `accuracy`/`f1_macro`/`roc_auc` metrics,
one demographic-parity-difference metric per protected attribute, a
`validation_report.json` artifact, and the fitted model under the `credit_default_model`
artifact path.

## Milestone 3 — Promote Registry Champion
Apply the acceptance thresholds and fairness ceilings to disqualify non-compliant
candidates, select the surviving candidate with the highest ROC-AUC, register it under
the dossier's registered model name, and assign it the `champion` alias in the MLflow
Model Registry. The highest-performing model overall is deliberately not the champion,
because it breaches a fairness ceiling.
