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

## 4. Milestone 3 — table `component_chains`

The **longest directed chain of components in the condensation DAG**. Contract every
strongly connected component (from milestone 2) to a single node identified by its
`component_id`. The *condensation* is the directed graph on these component nodes with
an edge `A -> B` iff some edge in `edges` runs from a node in component `A` to a node in
a **different** component `B`. Because each strongly connected component has been
contracted, the condensation is **acyclic** (a DAG).

For every component, `longest_chain` is the number of components on the **longest
directed path in the condensation that ends at that component** — i.e. counting the
component itself plus the most components that can be chained before it along
condensation edges. A component with no incoming condensation edge has
`longest_chain = 1`. Every component appears exactly once (one row per distinct
`component_id`, so the row count equals the number of strongly connected components).

| column | type |
|---|---|
| `component_id` | BIGINT (min node id of a strongly connected component, as in `components`) |
| `longest_chain` | BIGINT (components on the longest condensation path ending here, >= 1) |

All three result tables are written back into `/app/graph.duckdb`.
