#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: the CLI from milestone 1 persists at /app/signal_analysis.py.
# Run its `track` subcommand, which recomputes each valid experiment's analysis,
# (re)writes its measurements.csv and analysis.json, and logs one MLflow run per
# experiment to the sqlite store at /app/mlflow.db (artifacts under /app/mlruns).
python3 /app/signal_analysis.py track
