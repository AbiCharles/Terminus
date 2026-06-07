"""Prototype + validate the two new cycle-hard milestones:
   M2 = strongly connected components (component_id = min node in the SCC)
   M3 = shortest cycle length per node that lies on a cycle
against independent Python references, and time them.
"""

import time
from collections import defaultdict, deque

import duckdb

SCC_SQL = """
WITH RECURSIVE reach(a, b) AS (
    SELECT src, dst FROM edges
    UNION
    SELECT r.a, e.dst FROM reach r JOIN edges e ON e.src = r.b
),
mutual AS (
    SELECT r1.a AS x, r1.b AS y
    FROM reach r1 JOIN reach r2 ON r1.a = r2.b AND r1.b = r2.a
    UNION
    SELECT node_id, node_id FROM nodes
)
SELECT x AS node_id, MIN(y) AS component_id FROM mutual GROUP BY x
"""

# shortest cycle length per node on a cycle: min hops of a walk start->...->start.
# UNION (set) on (start,node,hops) with a hop bound keeps it finite despite cycles.
SHORTEST_CYCLE_SQL = """
WITH RECURSIVE walk(start, node, hops) AS (
    SELECT src, dst, 1 FROM edges
    UNION
    SELECT w.start, e.dst, w.hops + 1
    FROM walk w JOIN edges e ON e.src = w.node
    WHERE w.node <> w.start AND w.hops < (SELECT COUNT(*) FROM nodes)
)
SELECT start AS node_id, MIN(hops) AS shortest_cycle_len
FROM walk WHERE node = start GROUP BY start
"""


def py_scc(edges, node_ids):
    """Kosaraju: component_id = min node in each SCC."""
    adj, radj = defaultdict(list), defaultdict(list)
    for s, d in edges:
        adj[s].append(d)
        radj[d].append(s)
    visited, order = set(), []

    def dfs1(u):
        stack = [(u, iter(adj[u]))]
        visited.add(u)
        while stack:
            n, it = stack[-1]
            adv = next(it, None)
            if adv is None:
                order.append(n)
                stack.pop()
            elif adv not in visited:
                visited.add(adv)
                stack.append((adv, iter(adj[adv])))

    for u in node_ids:
        if u not in visited:
            dfs1(u)
    comp = {}
    for u in reversed(order):
        if u in comp:
            continue
        stack = [u]
        members = []
        comp[u] = u
        while stack:
            n = stack.pop()
            members.append(n)
            for v in radj[n]:
                if v not in comp:
                    comp[v] = u
                    stack.append(v)
        rep = min(members)
        for m in members:
            comp[m] = rep
    for u in node_ids:
        comp.setdefault(u, u)
    return comp


def py_shortest_cycle(edges, node_ids):
    adj = defaultdict(list)
    for s, d in edges:
        adj[s].append(d)
    out = {}
    for start in node_ids:
        dist = {start: 0}
        q = deque([start])
        found = None
        while q and found is None:
            u = q.popleft()
            for v in adj[u]:
                if v == start:
                    found = dist[u] + 1
                    break
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)
        if found is not None:
            out[start] = found
    return out


def main():
    con = duckdb.connect("graph.duckdb", read_only=True)
    edges = con.execute("SELECT src, dst FROM edges").fetchall()
    node_ids = [r[0] for r in con.execute("SELECT node_id FROM nodes ORDER BY node_id").fetchall()]

    t0 = time.time()
    scc = dict(con.execute(SCC_SQL).fetchall())
    t_scc = time.time() - t0
    ref_scc = py_scc(edges, node_ids)
    scc_match = scc == ref_scc
    n_nontrivial = len({c for c in ref_scc.values() if list(ref_scc.values()).count(c) > 1})
    print(f"M2 SCC: match={scc_match} time={t_scc:.2f}s nontrivial_components={n_nontrivial}")

    t0 = time.time()
    sc = dict(con.execute(SHORTEST_CYCLE_SQL).fetchall())
    t_sc = time.time() - t0
    ref_sc = py_shortest_cycle(edges, node_ids)
    sc_match = sc == ref_sc
    print(f"M3 shortest-cycle: match={sc_match} time={t_sc:.2f}s cycle_nodes={len(ref_sc)} "
          f"min={min(ref_sc.values()) if ref_sc else None} max={max(ref_sc.values()) if ref_sc else None}")
    con.close()


if __name__ == "__main__":
    main()
