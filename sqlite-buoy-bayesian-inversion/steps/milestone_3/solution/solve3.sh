#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: run the `invert` subcommand of the persisted /app/buoy_calibrate
# binary. It fits the heteroscedastic three-parameter change-point Gaussian posterior
# per buoy, writes /app/artifacts/<buoy_id>/posterior.json and /app/artifacts/summary.json,
# applies the §13 acceptance gate, and registers accepted buoys' correction models in
# /app/artifacts/registry.json (queryable via the `predict` subcommand).
/app/buoy_calibrate invert
