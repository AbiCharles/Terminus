"""Generate the graph + temporal DuckDB fixture for the recursive-CTE task.

Tables:
  nodes(node_id, label, category)
  edges(src, dst, weight)          -- directed, positive weights, CONTAINS CYCLES
  activations(node_id, ts)         -- per-node timestamped events (for sessionization)

The edge set deliberately includes back-edges so that naive recursive CTEs
(UNION ALL / no hop bound) loop forever; correct solutions must handle cycles.
"""

import numpy as np
import pandas as pd
import duckdb

RNG = np.random.default_rng(20240419)
N = 200
SRC = 1  # single source for shortest-path milestone

# ---- nodes ----
labels = [f"n{ i:03d}" for i in range(1, N + 1)]
category = RNG.choice(["service", "library", "tool"], size=N, p=[0.4, 0.45, 0.15])
nodes = pd.DataFrame({"node_id": np.arange(1, N + 1), "label": labels, "category": category})

# ---- edges: mostly forward (i -> j>i) for structure, plus back-edges to make cycles ----
edge_set = set()
# forward edges give a reachable, layered structure from the source
for i in range(1, N + 1):
    n_out = int(RNG.integers(0, 5))
    for _ in range(n_out):
        j = int(RNG.integers(i + 1, N + 1)) if i < N else i
        if j != i:
            edge_set.add((i, j))
# ensure source reaches a good chunk: connect 1 to several early nodes
for j in RNG.choice(range(2, 30), size=8, replace=False):
    edge_set.add((1, int(j)))
# inject back-edges (j -> i, j>i) to create cycles
for _ in range(40):
    a = int(RNG.integers(2, N + 1))
    b = int(RNG.integers(2, a)) if a > 2 else 2
    if a != b:
        edge_set.add((a, b))

edges = pd.DataFrame(sorted(edge_set), columns=["src", "dst"])

# ---- activations: per-node bursts separated by gaps (TIMESTAMP) ----
GAP_THRESHOLD_MIN = 30
base = np.datetime64("2026-01-01T00:00:00")
act_rows = []
active_nodes = RNG.choice(range(1, N + 1), size=140, replace=False)
for nid in active_nodes:
    t = base + np.timedelta64(int(RNG.integers(0, 60 * 24)), "m")
    n_sessions = int(RNG.integers(1, 5))
    for _ in range(n_sessions):
        burst = int(RNG.integers(1, 8))
        for _ in range(burst):
            act_rows.append((int(nid), t))
            # within-session gap is 1..30 INCLUSIVE; a gap of exactly 30 must NOT
            # split the session (the boundary is strictly greater than 30).
            t = t + np.timedelta64(int(RNG.integers(1, GAP_THRESHOLD_MIN + 1)), "m")
        # between-session gap: strictly greater than threshold
        t = t + np.timedelta64(int(RNG.integers(GAP_THRESHOLD_MIN + 1, 240)), "m")
activations = pd.DataFrame(act_rows, columns=["node_id", "ts"])
activations["ts"] = pd.to_datetime(activations["ts"])

if __name__ == "__main__":
    import os
    if os.path.exists("graph.duckdb"):
        os.remove("graph.duckdb")
    # small block size keeps the fixture well under the 1 MiB file limit
    con = duckdb.connect("graph.duckdb", config={"default_block_size": "16384"})
    for t in ("nodes", "edges", "activations"):
        con.execute(f"DROP TABLE IF EXISTS {t}")
    con.execute("CREATE TABLE nodes AS SELECT * FROM nodes")
    con.execute("CREATE TABLE edges AS SELECT * FROM edges")
    con.execute("CREATE TABLE activations AS SELECT * FROM activations")
    # quick cycle check
    has_cycle = con.execute(
        "SELECT COUNT(*) FROM edges a JOIN edges b ON a.dst=b.src AND b.dst=a.src"
    ).fetchone()[0]
    con.close()
    print("nodes", len(nodes), "edges", len(edges), "activations", len(activations))
    print("2-cycles (a<->b):", has_cycle, "| active nodes:", len(active_nodes))
    print("edges from source", SRC, ":", int((edges.src == SRC).sum()))
