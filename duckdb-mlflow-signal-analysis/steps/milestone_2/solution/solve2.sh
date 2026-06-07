#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: the CLI written in milestone 1 persists at
# /app/signal_analysis.py in the shared container. Run its `analyze` subcommand to
# compute, for every valid experiment, the detrended statistics, FFT-dominant
# frequencies, and seeded bootstrap RMS confidence interval into
# /app/artifacts/<id>/analysis.json.
python3 /app/signal_analysis.py analyze
