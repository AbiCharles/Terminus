"""Tests for milestone 3 (Longest Chain in the SCC Condensation).
Run alone with: pytest tests/test_m3.py

Verifies the agent's `component_chains` table gives, for every strongly connected
component, the length of the longest directed chain of components ending at it in the
condensation DAG, recomputed independently in Python (Kosaraju + topological DP),
per /app/spec.md §4.
"""

import duckdb
import pytest

import _reference

DB_PATH = "/app/graph.duckdb"


@pytest.fixture(scope="module")
def raw():
    return _reference.load()


@pytest.fixture(scope="module")
def agent_chains():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        rows = con.execute("SELECT component_id, longest_chain FROM component_chains").fetchall()
    finally:
        con.close()
    return rows


class TestMilestone3:
    """Milestone 3: longest condensation chain per strongly connected component."""

    def test_prior_artifacts_persist(self):
        """Milestone 1/2 tables must still exist (state persists)."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert {"reachability", "components"} <= tables, "earlier milestone tables missing"

    def test_one_row_per_component(self, agent_chains, raw):
        """There must be exactly one row per distinct component_id (= number of SCCs)."""
        nodes, edges = raw
        expected = _reference.condensation_longest_chains(edges, nodes)
        ids = [cid for cid, _ in agent_chains]
        assert len(ids) == len(set(ids)), "component_chains has duplicate component_id rows"
        assert set(ids) == set(expected), (
            "the set of component_ids does not match the strongly connected components "
            "(every component must appear exactly once)"
        )

    def test_chains_match_reference(self, agent_chains, raw):
        """Every component's longest_chain must match the independent topological recompute."""
        nodes, edges = raw
        expected = _reference.condensation_longest_chains(edges, nodes)
        actual = dict(agent_chains)
        wrong = {k: (actual.get(k), expected[k]) for k in expected if actual.get(k) != expected[k]}
        assert not wrong, (
            f"{len(wrong)} components have a wrong longest_chain "
            f"(e.g. {dict(list(wrong.items())[:3])})"
        )

    def test_nontrivial_chain_exists(self, agent_chains):
        """The condensation must chain multiple components (some longest_chain >= 2)."""
        assert any(length >= 2 for _, length in agent_chains), (
            "no longest_chain >= 2 found — the condensation should chain multiple components"
        )

    def test_lengths_are_positive(self, agent_chains):
        """Every longest_chain must be a positive integer (>= 1)."""
        assert all(length >= 1 for _, length in agent_chains), "longest_chain must be >= 1"
