#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle (pure SQL via the duckdb CLI): shortest cycle through each node on
# a cycle. A recursive walk carries its start node; it stops expanding once it returns to
# the start, and a hop bound keeps it finite despite cycles. The minimum hop count at which
# a walk returns to its start is that node's shortest cycle length (per /app/spec.md §4).
cat > /app/build_shortest_cycles.sql <<'SQL'
DROP TABLE IF EXISTS shortest_cycles;
CREATE TABLE shortest_cycles AS
WITH RECURSIVE walk(start, node, hops) AS (
    SELECT src, dst, 1 FROM edges
    UNION
    SELECT w.start, e.dst, w.hops + 1
    FROM walk w JOIN edges e ON e.src = w.node
    WHERE w.node <> w.start AND w.hops < (SELECT COUNT(*) FROM nodes)
)
SELECT start AS node_id, MIN(hops) AS shortest_cycle_len
FROM walk WHERE node = start GROUP BY start;
SELECT 'nodes on a cycle: ' || COUNT(*) AS summary FROM shortest_cycles;
SQL

duckdb /app/graph.duckdb < /app/build_shortest_cycles.sql
