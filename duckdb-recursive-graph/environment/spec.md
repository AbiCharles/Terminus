# Directed-Graph Analytics — Technical Specification

Binding contract for the pipeline. All table and column names and the output
definitions below are normative: the verifier reads/writes the same schemas and
recomputes the same quantities. Database: DuckDB at `/app/graph.duckdb`.

## 1. Source data

### Table `nodes`
| column | type | meaning |
|---|---|---|
| `node_id` | BIGINT | unique node id |
| `label` | VARCHAR | human label |
| `category` | VARCHAR | `service`, `library`, or `tool` |

### Table `edges` — directed graph, **contains cycles**
| column | type | meaning |
|---|---|---|
| `src` | BIGINT | edge tail (from) |
| `dst` | BIGINT | edge head (to) |

A directed edge `src -> dst`. The graph is **not acyclic** — it contains several
directed cycles — so any traversal must terminate correctly rather than loop forever.

## 2. Milestone 1 — table `reachability`

The transitive closure of the edge relation. `node_id` *reaches* `reachable_id` if
there is a directed path of one or more edges from `node_id` to `reachable_id`.
Because of cycles, a node reaches itself exactly when it lies on a cycle (so `(x, x)`
appears iff `x` is on a cycle). Each reachable pair appears once.

| column | type |
|---|---|
| `node_id` | BIGINT |
| `reachable_id` | BIGINT |

## 3. Milestone 2 — table `components`

Strongly connected components. Two nodes are in the same component when each can
reach the other (mutual reachability); every node is in the same component as
itself. Label each node with `component_id` = the **smallest `node_id`** among all
nodes in its component. One row per node.

| column | type |
|---|---|
| `node_id` | BIGINT |
| `component_id` | BIGINT (min node id of the node's strongly connected component) |

(A node not on any cycle forms a singleton component, so its `component_id` is its
own `node_id`.)

## 4. Milestone 3 — table `shortest_cycles`

For every node that lies on at least one directed cycle, the length of the
**shortest directed cycle through it** — the minimum number of edges on a directed
path that starts and ends at that node. Nodes that are not on any cycle do **not**
appear in this table.

| column | type |
|---|---|
| `node_id` | BIGINT |
| `shortest_cycle_len` | BIGINT (min edges on a cycle through the node, >= 1) |

All three result tables are written back into `/app/graph.duckdb`.
