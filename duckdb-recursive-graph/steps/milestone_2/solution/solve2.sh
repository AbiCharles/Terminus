#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: single-source minimum-hop distances from node 1 with a
# recursive CTE. The hop bound (< number of nodes) keeps the recursion finite
# despite cycles, and MIN(distance) per node collapses the levels to the shortest
# path (per /app/spec.md §3).
cat > /app/build_shortest_paths.py <<'PY'
"""Create the shortest_paths table: min hops from source node 1."""
import duckdb

con = duckdb.connect("/app/graph.duckdb")
con.execute("DROP TABLE IF EXISTS shortest_paths")
con.execute(
    """
    CREATE TABLE shortest_paths AS
    WITH RECURSIVE bfs(node_id, distance) AS (
        SELECT 1, 0
        UNION
        SELECT e.dst, b.distance + 1
        FROM bfs b JOIN edges e ON e.src = b.node_id
        WHERE b.distance < (SELECT COUNT(*) FROM nodes)
    )
    SELECT node_id, MIN(distance) AS distance
    FROM bfs GROUP BY node_id
    """
)
n = con.execute("SELECT COUNT(*) FROM shortest_paths").fetchone()[0]
con.close()
print(f"reachable-from-source nodes: {n}")
PY

python3 /app/build_shortest_paths.py
