#!/bin/bash
set -uo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set." >&2
  mkdir -p /logs/verifier
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

# The agent works in C++; the verifier-only deps (numpy/pytest/pytest-json-ctrf) are
# staged as wheels in the image and installed offline (no network, --no-index) from
# that wheel directory here at test time, then the milestone's pytest suite runs.
mkdir -p /logs/verifier
pip install --no-index --find-links=/opt/verifier-wheels \
    numpy==2.4.6 pytest==8.4.1 pytest-json-ctrf==0.3.5 >/dev/null 2>&1

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
