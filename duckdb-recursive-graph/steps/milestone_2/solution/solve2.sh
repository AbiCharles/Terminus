#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: strongly connected components. Compute the transitive
# closure, keep pairs that are mutually reachable (each reaches the other), add
# every node as mutually reachable with itself, then label each node with the
# minimum node id in its component (per /app/spec.md §3).
cat > /app/build_components.py <<'PY'
"""Create the components table (strongly connected components, min-id labelled)."""
import duckdb

con = duckdb.connect("/app/graph.duckdb")
con.execute("DROP TABLE IF EXISTS components")
con.execute(
    """
    CREATE TABLE components AS
    WITH RECURSIVE reach(node_id, reachable_id) AS (
        SELECT src, dst FROM edges
        UNION
        SELECT r.node_id, e.dst
        FROM reach r JOIN edges e ON e.src = r.reachable_id
    ),
    mutual AS (
        SELECT r1.node_id AS x, r1.reachable_id AS y
        FROM reach r1 JOIN reach r2
          ON r1.node_id = r2.reachable_id AND r1.reachable_id = r2.node_id
        UNION
        SELECT node_id, node_id FROM nodes
    )
    SELECT x AS node_id, MIN(y) AS component_id
    FROM mutual GROUP BY x
    """
)
n = con.execute("SELECT COUNT(DISTINCT component_id) FROM components").fetchone()[0]
con.close()
print(f"distinct components: {n}")
PY

python3 /app/build_components.py
