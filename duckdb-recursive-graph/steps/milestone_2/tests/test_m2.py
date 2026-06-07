"""Tests for milestone 2 (Strongly Connected Components).
Run alone with: pytest tests/test_m2.py

Verifies the agent's `components` table labels each node with the minimum node id
of its strongly connected component, recomputed independently with Kosaraju's
algorithm (/app/spec.md §3).
"""

import duckdb
import pytest

import _reference

DB_PATH = "/app/graph.duckdb"


@pytest.fixture(scope="module")
def raw():
    return _reference.load()


@pytest.fixture(scope="module")
def agent_components():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        rows = con.execute("SELECT node_id, component_id FROM components").fetchall()
    finally:
        con.close()
    return rows


class TestMilestone2:
    """Milestone 2: strongly connected components, labelled by minimum node id."""

    def test_reachability_persists(self):
        """The reachability table from milestone 1 must still exist (state persists)."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert "reachability" in tables, "reachability missing — was milestone 1 completed?"

    def test_one_row_per_node(self, agent_components, raw):
        """components must have exactly one row per node."""
        nodes, _ = raw
        mapping = dict(agent_components)
        assert len(agent_components) == len(mapping), "components has duplicate node_id rows"
        assert set(mapping) == set(nodes), "components must cover every node exactly once"

    def test_components_match_reference(self, agent_components, raw):
        """Every node's component_id must equal Kosaraju's min-id SCC label."""
        nodes, edges = raw
        expected = _reference.strongly_connected_components(edges, nodes)
        actual = dict(agent_components)
        wrong = {k: (actual[k], expected[k]) for k in expected if actual.get(k) != expected[k]}
        assert not wrong, f"{len(wrong)} nodes have a wrong component_id (e.g. {dict(list(wrong.items())[:3])})"

    def test_nontrivial_components_found(self, agent_components, raw):
        """Sanity: the cyclic structure yields several multi-node components."""
        nodes, edges = raw
        expected = _reference.strongly_connected_components(edges, nodes)
        sizes = {}
        for c in expected.values():
            sizes[c] = sizes.get(c, 0) + 1
        nontrivial = sum(1 for s in sizes.values() if s > 1)
        assert nontrivial >= 2, "fixture sanity: expected multiple non-trivial components"
        actual_nontrivial = {}
        for _, c in agent_components:
            actual_nontrivial[c] = actual_nontrivial.get(c, 0) + 1
        assert sum(1 for s in actual_nontrivial.values() if s > 1) == nontrivial, (
            "number of non-trivial components does not match the reference"
        )
