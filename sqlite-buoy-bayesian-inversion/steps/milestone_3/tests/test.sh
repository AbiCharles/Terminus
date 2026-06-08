#!/bin/bash
set -uo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set." >&2
  mkdir -p /logs/verifier
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

# Verifier-only test dependencies are staged as wheels in the image; install
# them offline (no network) from that wheel directory at test time.
mkdir -p /logs/verifier
pip install --no-index --find-links /opt/wheels numpy==2.4.6 pytest==8.4.1 pytest-json-ctrf==0.3.5

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
