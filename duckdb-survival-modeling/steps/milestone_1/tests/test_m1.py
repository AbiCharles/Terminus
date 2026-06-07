"""Tests for milestone 1 (Person-Period Table with LOCF + competing-risks outcome).
Run alone with: pytest tests/test_m1.py

Verifies the agent's `person_period` table is the exact discrete-time expansion of
`subjects` with the LOCF biomarker and the 3-class period_outcome (/app/spec.md §3),
recomputed independently from the raw tables.
"""

import duckdb
import pytest

import _reference

DB_PATH = "/app/survival.duckdb"
REQUIRED_COLUMNS = {
    "subject_id", "period", "age", "biomarker",
    "treatment", "stage", "sex", "split", "period_outcome",
}


@pytest.fixture(scope="module")
def raw():
    return _reference.load_tables()


@pytest.fixture(scope="module")
def agent_pp():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = con.execute("SELECT * FROM person_period").df()
    finally:
        con.close()
    return df


class TestMilestone1:
    """Milestone 1: discrete-time person-period table with LOCF biomarker."""

    def test_source_tables_intact(self, raw):
        """The source `subjects` (3000) and `measurements` tables must be intact (no tampering)."""
        subjects, measurements = raw
        assert len(subjects) == 3000, f"expected 3000 subjects, found {len(subjects)}"
        assert len(measurements) > 0, "measurements table is empty"

    def test_schema(self, agent_pp):
        """person_period must exist with the required columns, including the LOCF biomarker."""
        missing = REQUIRED_COLUMNS - set(agent_pp.columns)
        assert not missing, f"person_period missing columns: {missing}"

    def test_row_count(self, agent_pp, raw):
        """Row count must equal SUM(time_observed)."""
        subjects, _ = raw
        expected = int(subjects["time_observed"].sum())
        assert len(agent_pp) == expected, f"expected {expected} rows, found {len(agent_pp)}"

    def test_no_null_biomarker(self, agent_pp):
        """Every person-period row must carry an LOCF biomarker (no nulls)."""
        assert int(agent_pp["biomarker"].isna().sum()) == 0, "person_period has null biomarker values"

    def test_locf_and_outcome_match_reference(self, agent_pp, raw):
        """Each row's LOCF biomarker and period_outcome must match the reference expansion."""
        subjects, measurements = raw
        expected = _reference.expected_person_period(subjects, measurements)
        merged = expected.merge(
            agent_pp[["subject_id", "period", "biomarker", "period_outcome"]],
            on=["subject_id", "period"], how="outer", suffixes=("_ref", "_agent"), indicator=True,
        )
        unmatched = merged[merged["_merge"] != "both"]
        assert unmatched.empty, f"{len(unmatched)} (subject_id, period) rows do not align with the reference"
        bad_bio = merged[(merged["biomarker_ref"] - merged["biomarker_agent"]).abs() > 1e-9]
        assert bad_bio.empty, f"{len(bad_bio)} rows have an incorrect LOCF biomarker (wrong temporal join)"
        bad_out = merged[merged["period_outcome_ref"] != merged["period_outcome_agent"]]
        assert bad_out.empty, f"{len(bad_out)} rows have an incorrect period_outcome"

    def test_period_outcome_is_competing_risks_label(self, agent_pp):
        """period_outcome must be in {0,1,2} with at most one non-zero row per subject."""
        assert set(agent_pp["period_outcome"].unique()) <= {0, 1, 2}, "period_outcome must be 0/1/2"
        nonzero = agent_pp[agent_pp["period_outcome"] != 0].groupby("subject_id").size()
        assert (nonzero.max() if len(nonzero) else 0) <= 1, "no subject may have more than one event period"
