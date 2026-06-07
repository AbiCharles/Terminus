I've got a DuckDB database of a directed graph and I need three analytics tables built on top of it with SQL. The exact table schemas and output definitions are in `/app/spec.md` — read it first.

The database is at `/app/graph.duckdb`. It has `nodes` and `edges` (a directed graph that contains cycles). Over three milestones you'll build (1) the transitive reachability of the graph, (2) its strongly connected components, and (3) the shortest cycle through each node that lies on a cycle. Write every result table back into `/app/graph.duckdb`.

Milestone 1: build the `reachability` table defined in `/app/spec.md` — the transitive closure of the edge relation, i.e. every pair `(node_id, reachable_id)` where `reachable_id` is reachable from `node_id` by following one or more directed edges. The graph has cycles, so make sure your traversal terminates.
