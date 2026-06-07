#!/usr/bin/env bash
set -euo pipefail
cc -O2 -o /app/quake /app/quake.c -lsqlite3 -lm
/app/quake report --db /app/catalog.db --region Cascadia --out-prefix /app/report --window-years 50
echo "milestone 3: wrote /app/report_fmd.csv and /app/report_summary.json"
