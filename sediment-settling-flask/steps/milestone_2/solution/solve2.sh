#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: fetch every page of experiment 1's raw observations from the
# API, drop invalid readings, convert to physical units via the sensor
# calibration, and write /app/output/observations.csv (per /app/spec.md §3).
bash /app/start_api.sh
python3 /app/sediment_cli.py observations
