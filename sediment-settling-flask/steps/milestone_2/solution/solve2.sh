#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: ensure the API is up, then fetch + convert observations.
bash /app/start_api.sh
python3 /app/sediment_cli.py observations --experiment-id 7
