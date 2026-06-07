#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: build the transitive-reachability closure with a recursive
# CTE. UNION (set semantics) deduplicates discovered pairs so the recursion
# terminates even though the edge graph contains cycles (per /app/spec.md §2).
cat > /app/build_reachability.py <<'PY'
"""Create the reachability table (transitive closure of edges)."""
import duckdb

con = duckdb.connect("/app/graph.duckdb")
con.execute("DROP TABLE IF EXISTS reachability")
con.execute(
    """
    CREATE TABLE reachability AS
    WITH RECURSIVE reach(node_id, reachable_id) AS (
        SELECT src, dst FROM edges
        UNION
        SELECT r.node_id, e.dst
        FROM reach r JOIN edges e ON e.src = r.reachable_id
    )
    SELECT node_id, reachable_id FROM reach
    """
)
n = con.execute("SELECT COUNT(*) FROM reachability").fetchone()[0]
con.close()
print(f"reachability pairs: {n}")
PY

python3 /app/build_reachability.py
