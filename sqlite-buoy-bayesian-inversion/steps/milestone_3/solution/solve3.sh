#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: run `invert` to compute the conjugate Gaussian posterior for
# each buoy's offset and drift, writing /app/artifacts/<buoy_id>/posterior.json
# and the fleet-level /app/artifacts/summary.json.
python3 /app/buoy_calibrate.py invert
