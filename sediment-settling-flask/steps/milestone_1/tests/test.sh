#!/bin/bash
set -uo pipefail

# Ensure the observation API is running (the verifier queries it for ground truth).
bash /app/start_api.sh

# Verifier-only test deps are staged as wheels in the image; install offline.
mkdir -p /logs/verifier
pip install --no-index --find-links /opt/wheels pytest==8.4.1 pytest-json-ctrf==0.3.5

python -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_m1.py -rA
rc=$?

if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
