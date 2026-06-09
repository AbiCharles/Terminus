#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier

# Defensive: if launched at /, move to the task workdir (tests use absolute paths).
if [ "$PWD" = "/" ]; then
  cd /app || true
fi


# The agent works in C; the verifier-only pytest stack is staged as wheels in the image
# and installed offline (no network, --no-index) from that wheel directory here at test time.
pip install --no-index --find-links=/opt/verifier-wheels \
    pytest==8.4.1 pytest-json-ctrf==0.3.5 >/dev/null 2>&1

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
