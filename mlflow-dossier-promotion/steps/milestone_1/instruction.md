We're standing up a governed model-promotion pipeline for our credit team and I need you to drive it from our model-risk dossier. Everything you need is already on disk.

There's a long model-governance dossier at `/app/dossier.md` and a training dataset at `/app/data.csv`. Over three milestones you'll (1) turn the dossier's approval rules into a machine-readable policy, (2) train the candidate models the dossier registers and log them to a local MLflow tracking store, and (3) promote the one compliant champion into the MLflow Model Registry. Use MLflow with a sqlite backend at `sqlite:////app/mlflow.db` (artifacts under `/app/mlruns`) so the registry works. Read the dossier carefully — it has been revised several times and the older editions' numbers are still quoted in its case studies and appendices, but only the current edition's governing sections are binding.

Milestone 1: read `/app/dossier.md` and write the approval policy to `/app/policy.json` as a single JSON object with exactly this shape:

```json
{
  "registered_model_name": "<string>",
  "champion_alias": "<string>",
  "experiment_name": "<string>",
  "target_column": "<string>",
  "evaluation_split": "<string>",
  "model_artifact_path": "<string>",
  "data_split": {"train": <float>, "validation": <float>, "test": <float>, "stratify_on": "<string>", "random_state": <int>},
  "metric_thresholds": {"accuracy": <float>, "f1_macro": <float>, "roc_auc": <float>},
  "ranking_metric": "<string>",
  "feature_policy": {"numeric": [<string>...], "categorical": [<string>...], "prohibited": [<string>...]},
  "bias_slices": [{"column": "<string>", "metric": "<string>", "max_disparity": <float>}, ...],
  "candidates": [{"name": "<string>", "estimator": "<string>", "uses_prohibited_proxy": <bool>, "params": {<hyperparameters>}}, ...],
  "rollback_conditions": [{"id": "<string>", "metric": "<string>", "operator": "<string>", "threshold": <float>}, ...]
}
```

Fill every field with the binding values from the dossier: the registry identifiers and artifact path, the data-split protocol, the performance acceptance thresholds and the metric used to rank the champion, the approved and prohibited features, the fairness ceiling for each protected attribute, the full candidate roster with each model's estimator and hyperparameters, and the post-promotion rollback triggers. Be precise — superseded values from earlier editions must not appear.

Three disambiguations on the schema. First, `feature_policy.prohibited` is only for predictor fields the dossier forbids as model inputs; the approved predictors go in the numeric/categorical lists, and the protected attributes belong in `bias_slices`, not in `prohibited`. Second, `evaluation_split` is the name of the fold on which the dossier computes the acceptance metrics and fairness statistics — one of the values that appears in the dataset's `split` column — and not the name of the split column itself. Third, each `rollback_conditions` entry's `metric` must be the exact snake_case identifier the dossier gives for that trigger in its governing rollback section (e.g. `population_stability_index`, `weekly_approval_rate`, `roc_auc`) — not an abbreviation — and its `operator` is the comparison the trigger uses (`<` or `>`).
