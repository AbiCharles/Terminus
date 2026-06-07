#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier
# The verifier fetches from the observations API; make sure it is running.
bash /app/start_api.sh
# Verifier-only test deps are staged as wheels; install offline at test time.
pip install --no-index --find-links /opt/wheels pytest==8.4.1 pytest-json-ctrf==0.3.5

python -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_m2.py -rA
rc=$?

if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
