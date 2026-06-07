"""Tests for milestone 3 (Shortest Cycle Through Each Node).
Run alone with: pytest tests/test_m3.py

Verifies the agent's `shortest_cycles` table gives, for every node on a cycle, the
minimum cycle length through it, recomputed independently with Python BFS (/app/spec.md §4).
"""

import duckdb
import pytest

import _reference

DB_PATH = "/app/graph.duckdb"


@pytest.fixture(scope="module")
def raw():
    return _reference.load()


@pytest.fixture(scope="module")
def agent_cycles():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        rows = con.execute("SELECT node_id, shortest_cycle_len FROM shortest_cycles").fetchall()
    finally:
        con.close()
    return rows


class TestMilestone3:
    """Milestone 3: shortest directed cycle length per node on a cycle."""

    def test_prior_artifacts_persist(self):
        """Milestone 1/2 tables must still exist (state persists)."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert {"reachability", "components"} <= tables, "earlier milestone tables missing"

    def test_cycles_match_reference(self, agent_cycles, raw):
        """Exactly the nodes on cycles must appear, each with the correct shortest cycle length."""
        nodes, edges = raw
        expected = _reference.shortest_cycles(edges, nodes)
        actual = dict(agent_cycles)
        assert len(agent_cycles) == len(actual), "shortest_cycles has duplicate node_id rows"
        assert set(actual) == set(expected), (
            "the set of nodes on cycles does not match the reference "
            "(non-cycle nodes must be excluded; cycle nodes must all appear)"
        )
        wrong = {k: (actual[k], expected[k]) for k in expected if actual[k] != expected[k]}
        assert not wrong, f"{len(wrong)} nodes have a wrong shortest_cycle_len (e.g. {dict(list(wrong.items())[:3])})"

    def test_lengths_are_positive(self, agent_cycles):
        """Every shortest cycle length must be a positive integer."""
        assert all(length >= 1 for _, length in agent_cycles), "shortest_cycle_len must be >= 1"
