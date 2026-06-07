#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle (pure SQL via the duckdb CLI): build the transitive-reachability
# closure with a recursive CTE. UNION (set semantics) deduplicates discovered pairs so
# the recursion terminates even though the edge graph contains cycles (per /app/spec.md §2).
cat > /app/build_reachability.sql <<'SQL'
DROP TABLE IF EXISTS reachability;
CREATE TABLE reachability AS
WITH RECURSIVE reach(node_id, reachable_id) AS (
    SELECT src, dst FROM edges
    UNION
    SELECT r.node_id, e.dst
    FROM reach r JOIN edges e ON e.src = r.reachable_id
)
SELECT node_id, reachable_id FROM reach;
SELECT 'reachability pairs: ' || COUNT(*) AS summary FROM reachability;
SQL

duckdb /app/graph.duckdb < /app/build_reachability.sql
