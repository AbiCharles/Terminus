#!/bin/bash
# Idempotent launcher for the CFD Rails API on localhost:8000.
set -u
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  exit 0
fi
cd /opt/api || exit 1
nohup bundle exec puma -p 8000 config.ru > /tmp/pod_api.log 2>&1 &
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then exit 0; fi
  sleep 0.5
done
echo "CFD API failed to start; see /tmp/pod_api.log" >&2
exit 1
