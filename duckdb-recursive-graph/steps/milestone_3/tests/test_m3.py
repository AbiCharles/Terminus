"""Tests for milestone 3 (Activation Sessionization).
Run alone with: pytest tests/test_m3.py

Verifies the agent's `sessions` table groups activations into gaps-and-islands
sessions split on gaps strictly greater than 30 minutes, recomputed independently
with pandas (/app/spec.md §4).
"""

import duckdb
import pandas as pd
import pytest

import _reference

DB_PATH = "/app/graph.duckdb"


@pytest.fixture(scope="module")
def raw():
    return _reference.load()


@pytest.fixture(scope="module")
def agent_sessions():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = con.execute(
            "SELECT node_id, session_index, start_ts, end_ts, num_events FROM sessions"
        ).df()
    finally:
        con.close()
    return df


class TestMilestone3:
    """Milestone 3: activation sessionization (gaps-and-islands)."""

    def test_prior_artifacts_persist(self):
        """Milestone 1/2 tables must still exist (state persists)."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        finally:
            con.close()
        assert {"reachability", "shortest_paths"} <= tables, "earlier milestone tables missing"

    def test_schema_and_row_count(self, agent_sessions, raw):
        """sessions must have the required columns and the reference number of rows."""
        _, _, activations = raw
        assert {"node_id", "session_index", "start_ts", "end_ts", "num_events"} <= set(agent_sessions.columns)
        expected = _reference.sessions(activations)
        assert len(agent_sessions) == len(expected), (
            f"expected {len(expected)} sessions, found {len(agent_sessions)} "
            "(check the strictly-greater-than-30-minutes boundary)"
        )

    def test_sessions_match_reference(self, agent_sessions, raw):
        """Each (node_id, session_index) must match the reference start/end/num_events exactly."""
        _, _, activations = raw
        expected = _reference.sessions(activations)
        exp = expected.set_index(["node_id", "session_index"]).sort_index()
        got = agent_sessions.copy()
        got["start_ts"] = pd.to_datetime(got["start_ts"])
        got["end_ts"] = pd.to_datetime(got["end_ts"])
        got = got.set_index(["node_id", "session_index"]).sort_index()
        assert set(got.index) == set(exp.index), "session keys (node_id, session_index) do not match"
        joined = exp.join(got, rsuffix="_agent")
        bad_n = joined[joined["num_events"] != joined["num_events_agent"]]
        assert bad_n.empty, f"{len(bad_n)} sessions have a wrong num_events"
        bad_start = joined[joined["start_ts"] != joined["start_ts_agent"]]
        bad_end = joined[joined["end_ts"] != joined["end_ts_agent"]]
        assert bad_start.empty and bad_end.empty, "session start_ts/end_ts do not match the reference"

    def test_session_index_starts_at_one(self, agent_sessions):
        """Each node's session numbering must start at 1."""
        first = agent_sessions.groupby("node_id")["session_index"].min()
        assert (first == 1).all(), "session_index must start at 1 for every node"
