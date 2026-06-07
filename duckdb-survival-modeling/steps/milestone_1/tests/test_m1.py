"""Tests for milestone 1 (Build Person-Period Feature Table).
Run alone with: pytest tests/test_m1.py

Verifies that the agent's `person_period` table is the exact discrete-time
expansion of `subjects` defined in /app/spec.md §3, recomputed independently.
"""

import duckdb
import pytest

import _reference

DB_PATH = "/app/survival.duckdb"
REQUIRED_COLUMNS = {
    "subject_id", "period", "age", "biomarker",
    "treatment", "stage", "sex", "split", "event_in_period",
}


@pytest.fixture(scope="module")
def subjects():
    return _reference.load_subjects()


@pytest.fixture(scope="module")
def agent_pp():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = con.execute("SELECT * FROM person_period").df()
    finally:
        con.close()
    return df


class TestMilestone1:
    """Milestone 1: the discrete-time person-period table built from `subjects`."""

    def test_subjects_table_intact(self, subjects):
        """The source `subjects` table must still hold all 3000 rows (no tampering)."""
        assert len(subjects) == 3000, f"expected 3000 subjects, found {len(subjects)}"

    def test_person_period_exists_with_schema(self, agent_pp):
        """`person_period` must exist and contain the required columns (§3)."""
        missing = REQUIRED_COLUMNS - set(agent_pp.columns)
        assert not missing, f"person_period missing columns: {missing}"

    def test_row_count_equals_sum_time_observed(self, agent_pp, subjects):
        """Row count must equal SUM(time_observed) over all subjects."""
        expected = int(subjects["time_observed"].sum())
        assert len(agent_pp) == expected, f"expected {expected} rows, found {len(agent_pp)}"

    def test_expansion_matches_reference(self, agent_pp, subjects):
        """Each (subject_id, period) row and its event_in_period must match the reference expansion."""
        expected = _reference.expected_person_period(subjects)
        merged = expected.merge(
            agent_pp[["subject_id", "period", "event_in_period"]],
            on=["subject_id", "period"], how="outer", suffixes=("_ref", "_agent"), indicator=True,
        )
        unmatched = merged[merged["_merge"] != "both"]
        assert unmatched.empty, f"{len(unmatched)} (subject_id, period) rows do not align with the reference"
        bad = merged[merged["event_in_period_ref"] != merged["event_in_period_agent"]]
        assert bad.empty, f"{len(bad)} rows have an incorrect event_in_period flag"

    def test_event_in_period_is_binary(self, agent_pp):
        """event_in_period must be 0/1, with exactly one 1 per subject that had an event."""
        assert set(agent_pp["event_in_period"].unique()) <= {0, 1}, "event_in_period must be 0/1"
        per_subject = agent_pp.groupby("subject_id")["event_in_period"].sum()
        assert per_subject.max() <= 1, "no subject may have more than one event period"
