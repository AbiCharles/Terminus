"""Tests for milestone 1 (Transitive Reachability).
Run alone with: pytest tests/test_m1.py

Verifies the agent's `reachability` table is the exact transitive closure of
`edges` (cycles handled), recomputed independently with Python BFS (/app/spec.md §2).
"""

import duckdb
import pytest

import _reference

DB_PATH = "/app/graph.duckdb"


@pytest.fixture(scope="module")
def raw():
    return _reference.load()


@pytest.fixture(scope="module")
def agent_pairs():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        rows = con.execute("SELECT node_id, reachable_id FROM reachability").fetchall()
    finally:
        con.close()
    return rows


class TestMilestone1:
    """Milestone 1: transitive reachability closure over a cyclic graph."""

    def test_source_tables_intact(self, raw):
        """The source nodes/edges tables must be intact (200 nodes; edges present)."""
        nodes, edges, _ = raw
        assert len(nodes) == 200, f"expected 200 nodes, found {len(nodes)}"
        assert len(edges) > 0, "edges table is empty"

    def test_reachability_matches_reference(self, agent_pairs, raw):
        """The set of (node_id, reachable_id) pairs must equal the BFS transitive closure."""
        _, edges, _ = raw
        expected = _reference.reachability_pairs(edges)
        actual = set(agent_pairs)
        assert len(agent_pairs) == len(actual), "reachability contains duplicate pairs"
        missing = expected - actual
        extra = actual - expected
        assert not missing, f"{len(missing)} reachable pairs are missing (e.g. {sorted(missing)[:3]})"
        assert not extra, f"{len(extra)} spurious pairs present (e.g. {sorted(extra)[:3]})"

    def test_cycle_self_pairs_present(self, agent_pairs, raw):
        """A node appears as its own reachable target iff it lies on a cycle (non-trivial closure)."""
        _, edges, _ = raw
        expected_self = {a for (a, b) in _reference.reachability_pairs(edges) if a == b}
        actual_self = {a for (a, b) in agent_pairs if a == b}
        assert expected_self, "fixture sanity: there should be nodes on cycles"
        assert actual_self == expected_self, "self-reachable (cycle) nodes do not match the reference"
