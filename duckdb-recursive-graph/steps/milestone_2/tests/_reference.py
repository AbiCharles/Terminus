"""Independent reference for the recursive-graph task.

Recomputes, from the raw `nodes` and `edges` tables alone, the transitive
reachability closure, the strongly connected components (min-id labelled), and the
longest directed chain of components in the SCC condensation DAG — using plain Python
(BFS + Kosaraju + topological DP), a different method than the agent's recursive SQL.
It is the verifier's answer key; the agent has no access to it.
"""

from collections import defaultdict, deque

import duckdb

DB_PATH = "/app/graph.duckdb"


def load():
    con = duckdb.connect(DB_PATH, read_only=True)
    nodes = [r[0] for r in con.execute("SELECT node_id FROM nodes ORDER BY node_id").fetchall()]
    edges = con.execute("SELECT src, dst FROM edges").fetchall()
    con.close()
    return nodes, edges


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


def strongly_connected_components(edges, node_ids):
    """Kosaraju; returns dict node -> component_id (min node id in its SCC)."""
    adj, radj = defaultdict(list), defaultdict(list)
    for s, d in edges:
        adj[s].append(d)
        radj[d].append(s)
    visited, order = set(), []
    for u in node_ids:
        if u in visited:
            continue
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
    comp = {}
    for u in reversed(order):
        if u in comp:
            continue
        members, stack = [], [u]
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


def shortest_cycles(edges, node_ids):
    """BFS from each node back to itself; returns dict node -> shortest cycle length."""
    adj = adjacency(edges)
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


def condensation_longest_chains(edges, node_ids):
    """Longest directed chain of SCCs ending at each component, over the condensation DAG.

    Contract each strongly connected component to a single node (labelled by its
    min node id). The condensation has a directed edge A -> B iff some graph edge runs
    from a node in component A to a node in a different component B; it is acyclic. For
    every component C, returns the number of components on the longest directed path in
    the condensation that ends at C (a component with no incoming condensation edge has
    chain length 1). Computed by topological dynamic programming, independently of the
    agent's recursive SQL.
    """
    comp = strongly_connected_components(edges, node_ids)
    comps = set(comp.values())
    preds = {c: set() for c in comps}
    succs = {c: set() for c in comps}
    for s, d in edges:
        ca, cb = comp[s], comp[d]
        if ca != cb:
            preds[cb].add(ca)
            succs[ca].add(cb)
    # Kahn topological order over the condensation DAG.
    indeg = {c: len(preds[c]) for c in comps}
    queue = deque(sorted(c for c in comps if indeg[c] == 0))
    longest = {c: 1 for c in comps}
    order = []
    while queue:
        c = queue.popleft()
        order.append(c)
        for nb in sorted(succs[c]):
            if longest[c] + 1 > longest[nb]:
                longest[nb] = longest[c] + 1
            indeg[nb] -= 1
            if indeg[nb] == 0:
                queue.append(nb)
    return longest
