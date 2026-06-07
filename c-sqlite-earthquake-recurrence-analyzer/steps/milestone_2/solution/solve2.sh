#!/usr/bin/env bash
set -euo pipefail
# The full CLI was written in milestone 1; recompile idempotently in case this
# milestone is run on its own, then exercise the `stats` subcommand.
cc -O2 -o /app/quake /app/quake.c -lsqlite3 -lm
/app/quake stats --db /app/catalog.db --region Cascadia --out /app/stats.json
echo "milestone 2: wrote /app/stats.json"
