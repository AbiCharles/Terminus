#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: run the `query` subcommand of the C++ program compiled in
# milestone 1 (the /app/buoy_calibrate binary persists in the shared container). It
# reads /app/observations.db with the protocol from milestone 1 and writes the cleaned
# per-buoy residual series to /app/artifacts/<buoy_id>/clean.csv.
/app/buoy_calibrate query
