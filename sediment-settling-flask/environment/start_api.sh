#!/usr/bin/env bash
# Idempotently start the settling-observation API on 127.0.0.1:8000.
# Safe to call repeatedly: returns immediately if the API is already up.
set -u
PORT=8000
URL="http://127.0.0.1:${PORT}/health"

is_up() {
  python3 - "$URL" <<'PY' 2>/dev/null
import sys, urllib.request
try:
    urllib.request.urlopen(sys.argv[1], timeout=1).read()
except Exception:
    sys.exit(1)
PY
}

if is_up; then
  exit 0
fi

nohup python3 /app/api/server.py > /tmp/sediment_api.log 2>&1 &
for _ in $(seq 1 60); do
  if is_up; then
    exit 0
  fi
  sleep 0.25
done
echo "sediment API failed to start; see /tmp/sediment_api.log" >&2
exit 1
