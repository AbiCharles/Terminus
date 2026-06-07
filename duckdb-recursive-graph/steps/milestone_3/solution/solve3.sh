#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle (pure SQL via the duckdb CLI): longest directed chain of components
# in the SCC condensation DAG. Build the condensation edges (edges between DISTINCT
# components, from milestone 2's `components` table), then a recursive walk extends every
# chain along condensation edges, carrying its length; because the condensation is acyclic
# the recursion terminates. The longest chain ENDING at each component is the MAX length
# over all chains that reach it (per /app/spec.md §4).
cat > /app/build_component_chains.sql <<'SQL'
DROP TABLE IF EXISTS component_chains;
CREATE TABLE component_chains AS
WITH RECURSIVE
cond_edges AS (
    SELECT DISTINCT c1.component_id AS ca, c2.component_id AS cb
    FROM edges e
    JOIN components c1 ON e.src = c1.node_id
    JOIN components c2 ON e.dst = c2.node_id
    WHERE c1.component_id <> c2.component_id
),
chain(comp, len) AS (
    SELECT DISTINCT component_id, 1 FROM components
    UNION ALL
    SELECT ce.cb, ch.len + 1
    FROM chain ch JOIN cond_edges ce ON ce.ca = ch.comp
)
SELECT comp AS component_id, MAX(len) AS longest_chain
FROM chain
GROUP BY comp;
SELECT 'components: ' || COUNT(*) || ', longest chain: ' || MAX(longest_chain) AS summary
FROM component_chains;
SQL

duckdb /app/graph.duckdb < /app/build_component_chains.sql
