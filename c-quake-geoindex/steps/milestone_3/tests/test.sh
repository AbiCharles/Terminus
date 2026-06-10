#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

# Defensive: if launched at /, move to the task workdir (tests use absolute paths).
if [ "$PWD" = "/" ]; then
  cd /app || true
fi

# pytest + pytest-json-ctrf are preinstalled in the image. Disable errexit around
# the test run so a failing test still reaches the reward-writing section below.
set +e
python -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_m3.py -rA
rc=$?
if [ "$rc" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
