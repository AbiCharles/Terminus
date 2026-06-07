"""Validate the three recursive/window SQL queries against independent Python
references, check that cycles exist, and time the queries."""

import time
from collections import defaultdict, deque

import duckdb
import pandas as pd

SRC = 1
GAP_MIN = 30

REACH_SQL = """
WITH RECURSIVE reach(node, reachable) AS (
    SELECT src, dst FROM edges
    UNION
    SELECT r.node, e.dst FROM reach r JOIN edges e ON e.src = r.reachable
)
SELECT node AS node_id, reachable AS reachable_id FROM reach
"""

SHORTEST_SQL = """
WITH RECURSIVE bfs(node, hops) AS (
    SELECT 1, 0
    UNION
    SELECT e.dst, b.hops + 1
    FROM bfs b JOIN edges e ON e.src = b.node
    WHERE b.hops < (SELECT COUNT(*) FROM nodes)
)
SELECT node AS node_id, MIN(hops) AS distance FROM bfs GROUP BY node
"""

SESSION_SQL = """
WITH ordered AS (
    SELECT node_id, ts,
           LAG(ts) OVER (PARTITION BY node_id ORDER BY ts) AS prev_ts
    FROM activations
),
flagged AS (
    SELECT node_id, ts,
           CASE WHEN prev_ts IS NULL OR ts - prev_ts > INTERVAL 30 MINUTE THEN 1 ELSE 0 END AS is_new
    FROM ordered
),
numbered AS (
    SELECT node_id, ts, SUM(is_new) OVER (PARTITION BY node_id ORDER BY ts
                                          ROWS UNBOUNDED PRECEDING) AS session_index
    FROM flagged
)
SELECT node_id, session_index, MIN(ts) AS start_ts, MAX(ts) AS end_ts, COUNT(*) AS num_events
FROM numbered GROUP BY node_id, session_index
"""


def py_reachability(edges):
    adj = defaultdict(list)
    for s, d in edges:
        adj[s].append(d)
    pairs = set()
    nodes = {s for s, _ in edges} | {d for _, d in edges}
    for start in nodes:
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


def py_shortest(edges, src, n):
    """Unweighted shortest path (min hops) from src via BFS; includes src at 0."""
    adj = defaultdict(list)
    for s, d in edges:
        adj[s].append(d)
    dist = {src: 0}
    q = deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def main():
    con = duckdb.connect("graph.duckdb", read_only=True)
    edges = con.execute("SELECT src, dst FROM edges").fetchall()
    n = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    t0 = time.time()
    reach = con.execute(REACH_SQL).df()
    t_reach = time.time() - t0
    py_reach = py_reachability(edges)
    sql_reach = set(map(tuple, reach[["node_id", "reachable_id"]].itertuples(index=False, name=None)))
    cycles = sum(1 for (a, b) in py_reach if a == b)
    print(f"M1 reachability: sql={len(sql_reach)} py={len(py_reach)} match={sql_reach == py_reach} "
          f"self-loops(cycle nodes)={cycles} time={t_reach:.2f}s")

    t0 = time.time()
    sp = con.execute(SHORTEST_SQL).df()
    t_sp = time.time() - t0
    py_sp = py_shortest(edges, SRC, n)
    sql_sp = dict(zip(sp["node_id"], sp["distance"]))
    match_sp = all(abs(py_sp.get(k, -1) - v) < 1e-9 for k, v in sql_sp.items()) and set(sql_sp) == set(py_sp)
    print(f"M2 shortest: sql_nodes={len(sql_sp)} py_nodes={len(py_sp)} match={match_sp} time={t_sp:.2f}s")

    sess = con.execute(SESSION_SQL).df()
    acts = con.execute("SELECT node_id, ts FROM activations ORDER BY node_id, ts").df()
    con.close()
    # independent pandas sessionization (gap > 30 min => new session)
    acts = acts.sort_values(["node_id", "ts"])
    gap = acts.groupby("node_id")["ts"].diff()
    acts["is_new"] = gap.isna() | (gap > pd.Timedelta(minutes=30))
    acts["session_index"] = acts.groupby("node_id")["is_new"].cumsum()
    py_sess = acts.groupby(["node_id", "session_index"]).agg(
        start_ts=("ts", "min"), end_ts=("ts", "max"), num_events=("ts", "size")).reset_index()
    exactly_30 = int((gap == pd.Timedelta(minutes=30)).sum())
    sess_match = len(sess) == len(py_sess)
    print(f"M3 sessions: sql_rows={len(sess)} py_rows={len(py_sess)} match={sess_match} "
          f"exactly-30min-gaps(must NOT split)={exactly_30}")


if __name__ == "__main__":
    main()
