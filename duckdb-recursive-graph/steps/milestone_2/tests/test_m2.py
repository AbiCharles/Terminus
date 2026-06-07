"""Tests for milestone 2 (Single-Source Shortest Paths).
Run alone with: pytest tests/test_m2.py

Verifies the agent's `shortest_paths` table gives the minimum hop distance from
node 1 to every reachable node, recomputed independently with Python BFS (/app/spec.md §3).
"""

import duckdb
import pytest

import _reference

DB_PATH = "/app/graph.duckdb"


@pytest.fixture(scope="module")
def raw():
    return _reference.load()


@pytest.fixture(scope="module")
def agent_dist():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        rows = con.execute("SELECT node_id, distance FROM shortest_paths").fetchall()
    finally:
        con.close()
    return rows


class TestMilestone2:
    """Milestone 2: minimum-hop shortest paths from the source node."""

    def test_reachability_persists(self):
        """The reachability table from milestone 1 must still exist (state persists)."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert "reachability" in tables, "reachability missing — was milestone 1 completed?"

    def test_distances_match_reference(self, agent_dist, raw):
        """node->distance must equal BFS min-hops from node 1 (same node set, same values)."""
        _, edges, _ = raw
        expected = _reference.shortest_from_source(edges)
        actual = dict(agent_dist)
        assert len(agent_dist) == len(actual), "shortest_paths has duplicate node_id rows"
        assert set(actual) == set(expected), (
            "the set of reachable nodes does not match BFS from the source"
        )
        wrong = {k: (actual[k], expected[k]) for k in expected if actual[k] != expected[k]}
        assert not wrong, f"{len(wrong)} nodes have a wrong distance (e.g. {dict(list(wrong.items())[:3])})"

    def test_source_distance_zero(self, agent_dist):
        """The source node 1 must be present with distance 0."""
        actual = dict(agent_dist)
        assert actual.get(1) == 0, "source node 1 must appear with distance 0"
