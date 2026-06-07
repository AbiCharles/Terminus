#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: the CLI and protocol.json from milestone 1 persist in the
# shared container. Run `query` to write each calibrated buoy's cleaned residual
# series to /app/artifacts/<buoy_id>/clean.csv.
python3 /app/buoy_calibrate.py query
