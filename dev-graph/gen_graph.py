"""Generate the directed-graph DuckDB fixture for the recursive-CTE task.

Structure: a forward DAG (edges i -> j>i, which never form cycles on their own)
plus several DISJOINT directed rings on consecutive-node windows. Each ring is its
own strongly connected component, so the only cycles in the graph are these rings.
This yields a rich SCC structure and well-defined shortest cycles, while naive
recursive CTEs (UNION ALL / no hop bound) still loop forever on the rings.

Tables:
  nodes(node_id, label, category)
  edges(src, dst)
"""

import os

import numpy as np
import pandas as pd
import duckdb

RNG = np.random.default_rng(20240607)
N = 200

labels = [f"n{i:03d}" for i in range(1, N + 1)]
category = RNG.choice(["service", "library", "tool"], size=N, p=[0.4, 0.45, 0.15])
nodes = pd.DataFrame({"node_id": np.arange(1, N + 1), "label": labels, "category": category})

edge_set = set()

# forward DAG edges (strictly increasing node id -> acyclic by themselves)
for i in range(1, N + 1):
    for _ in range(int(RNG.integers(0, 4))):
        if i < N:
            j = int(RNG.integers(i + 1, N + 1))
            edge_set.add((i, j))
# make sure node 1 reaches a good chunk
for j in RNG.choice(range(2, 40), size=10, replace=False):
    edge_set.add((1, int(j)))

# disjoint directed rings -> the only cycles / SCCs in the graph
ring_windows = []
start = 12
RNG_sizes = RNG.integers(3, 6, size=9)
for size in RNG_sizes:
    size = int(size)
    if start + size > N - 5:
        break
    window = list(range(start, start + size))
    ring_windows.append(window)
    for a, b in zip(window, window[1:] + window[:1]):  # a->b around the ring
        edge_set.add((a, b))
    start += size + int(RNG.integers(8, 18))  # gap to keep rings disjoint/separate

edges = pd.DataFrame(sorted(edge_set), columns=["src", "dst"])

if __name__ == "__main__":
    if os.path.exists("graph.duckdb"):
        os.remove("graph.duckdb")
    con = duckdb.connect("graph.duckdb", config={"default_block_size": "16384"})
    con.execute("CREATE TABLE nodes AS SELECT * FROM nodes")
    con.execute("CREATE TABLE edges AS SELECT * FROM edges")
    con.close()
    print("nodes", len(nodes), "edges", len(edges), "rings", len(ring_windows),
          "ring_sizes", [len(w) for w in ring_windows])
    print("ring windows:", ring_windows)
