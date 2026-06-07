# Graph & Activity Analytics — Technical Specification

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

A directed edge `src -> dst` means `src` depends on `dst`. The edge set is **not
acyclic**: it contains directed cycles, so any traversal must terminate correctly
rather than loop forever.

### Table `activations` — timestamped events
| column | type | meaning |
|---|---|---|
| `node_id` | BIGINT | the node that was active |
| `ts` | TIMESTAMP | activation time |

## 2. Milestone 1 — table `reachability`

The transitive closure of the edge relation. `node_id` *reaches* `reachable_id`
if there is a directed path of one or more edges from `node_id` to `reachable_id`.
Because the graph contains cycles, a node reaches itself exactly when it lies on a
cycle (so `(x, x)` appears iff `x` is on a cycle). Each reachable pair appears once.

| column | type |
|---|---|
| `node_id` | BIGINT |
| `reachable_id` | BIGINT |

## 3. Milestone 2 — table `shortest_paths`

Single-source shortest paths from the **source node `node_id = 1`**, measured as
the minimum number of edges (hops) along any directed path. Include one row per
node that is reachable from the source, **including the source itself at distance 0**.
A node not reachable from the source does not appear. `distance` is the minimum hop
count over all directed paths (paths through cycles never reduce the minimum).

| column | type |
|---|---|
| `node_id` | BIGINT |
| `distance` | BIGINT (minimum hops from node 1) |

## 4. Milestone 3 — table `sessions`

Group each node's activations into sessions. Order each node's activations by `ts`.
A new session begins at an activation whose gap from the **previous** activation of
the same node is **strictly greater than 30 minutes**. A gap of *exactly* 30 minutes
does **not** start a new session (it stays in the current one). The first activation
of a node begins session 1; `session_index` increases by 1 at each new session for
that node.

One row per `(node_id, session_index)`:

| column | type |
|---|---|
| `node_id` | BIGINT |
| `session_index` | BIGINT (1, 2, … per node) |
| `start_ts` | TIMESTAMP (earliest activation in the session) |
| `end_ts` | TIMESTAMP (latest activation in the session) |
| `num_events` | BIGINT (activations in the session) |

All three result tables are written back into `/app/graph.duckdb`.
