"""Independent reference for the recursive-graph + sessionization task.

Recomputes, from the raw `nodes`, `edges`, and `activations` tables alone, the
transitive reachability closure, the single-source minimum-hop distances, and the
activation sessions — using plain Python BFS and pandas (a different method than
the agent's SQL). It is the verifier's answer key; the agent has no access to it.
"""

from collections import defaultdict, deque

import duckdb
import pandas as pd

DB_PATH = "/app/graph.duckdb"
SOURCE = 1
GAP_MINUTES = 30


def load():
    con = duckdb.connect(DB_PATH, read_only=True)
    nodes = con.execute("SELECT * FROM nodes").df()
    edges = con.execute("SELECT src, dst FROM edges").fetchall()
    activations = con.execute("SELECT node_id, ts FROM activations").df()
    con.close()
    return nodes, edges, activations


def adjacency(edges):
    adj = defaultdict(list)
    for s, d in edges:
        adj[s].append(d)
    return adj


def reachability_pairs(edges):
    """Set of (node, reachable) pairs; (x, x) only when x is on a cycle."""
    adj = adjacency(edges)
    starts = {s for s, _ in edges} | {d for _, d in edges}
    pairs = set()
    for start in starts:
        seen = set()
        q = deque(adj[start])
        while q:
            x = q.popleft()
            if x in seen:
                continue
            seen.add(x)
            q.extend(adj[x])
        for r in seen:
            pairs.add((start, r))
    return pairs


def shortest_from_source(edges, source=SOURCE):
    """Min hops from source via BFS; dict node -> distance, includes source at 0."""
    adj = adjacency(edges)
    dist = {source: 0}
    q = deque([source])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def sessions(activations):
    """Gaps-and-islands: new session when gap strictly > 30 minutes."""
    acts = activations.sort_values(["node_id", "ts"]).copy()
    gap = acts.groupby("node_id")["ts"].diff()
    acts["is_new"] = gap.isna() | (gap > pd.Timedelta(minutes=GAP_MINUTES))
    acts["session_index"] = acts.groupby("node_id")["is_new"].cumsum()
    out = acts.groupby(["node_id", "session_index"]).agg(
        start_ts=("ts", "min"), end_ts=("ts", "max"), num_events=("ts", "size"),
    ).reset_index()
    return out
