#!/bin/bash
set -uo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set." >&2
  exit 1
fi

# Verifier-only test dependencies are staged as wheels in the image; install
# them offline (no network) from that wheel directory at test time. The C
# toolchain (gcc) used to build the VM under UBSan is part of the image, so no
# network access is required here.
mkdir -p /logs/verifier
pip install --no-index --find-links /opt/wheels pytest==8.4.1 pytest-json-ctrf==0.3.5

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
