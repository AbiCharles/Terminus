#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier

# Defensive: a container that starts at / has no working directory set.
if [ "$PWD" = "/" ]; then
  echo "Error: no working directory set (expected /app)."
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

# them offline (no network) from that wheel directory at test time.

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
