#!/usr/bin/env bash
# Idempotent launcher for the settling-column observations API. Starts it in the
# background if not already serving, then waits for /health. Safe to call repeatedly.
set -uo pipefail
PORT=8000
check() {
    python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/health', timeout=1)" 2>/dev/null
}
if check; then exit 0; fi
nohup python3 /app/api/server.py > /tmp/api.log 2>&1 &
for _ in $(seq 1 50); do
    if check; then exit 0; fi
    sleep 0.2
done
echo "API failed to start; log follows:" >&2; cat /tmp/api.log >&2; exit 1
