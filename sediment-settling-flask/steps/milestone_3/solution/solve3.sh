#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: fit the settling model to the milestone-2 observations and
# write /app/output/report.json with parameters, 95% CIs, derived velocity and
# Stokes effective diameter, and residual metrics (per /app/spec.md §4).
python3 /app/sediment_cli.py fit
