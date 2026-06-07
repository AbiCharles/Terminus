"""Tests for milestone 2 (Retrieve Settling Observations).
Run alone with: pytest tests/test_m2.py

Verifies /app/output/observations.csv contains every valid observation for
experiment 1 — all pages fetched, invalid readings dropped, raw units converted —
matching an independent paginated fetch + conversion (/app/spec.md §3).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import _reference

CSV_PATH = Path("/app/output/observations.csv")


@pytest.fixture(scope="module")
def agent_csv():
    assert CSV_PATH.exists(), "/app/output/observations.csv does not exist — milestone 2 not completed"
    return pd.read_csv(CSV_PATH)


@pytest.fixture(scope="module")
def reference_rows():
    return _reference.observations()


class TestMilestone2:
    """Milestone 2: paginated fetch + unit conversion + invalid filtering."""

    def test_metadata_persists(self):
        """metadata.json from milestone 1 must still exist (state persists)."""
        assert Path("/app/output/metadata.json").exists(), "metadata.json missing — was milestone 1 completed?"

    def test_header(self, agent_csv):
        """observations.csv must have exactly the header time_s,height_cm."""
        assert list(agent_csv.columns) == ["time_s", "height_cm"], "header must be time_s,height_cm"

    def test_row_count_matches_valid_total(self, agent_csv, reference_rows):
        """Row count must equal the number of VALID observations across ALL pages."""
        assert len(agent_csv) == len(reference_rows), (
            f"expected {len(reference_rows)} valid rows, found {len(agent_csv)} "
            "(check that every page was fetched and invalid readings were dropped)"
        )

    def test_values_match_reference(self, agent_csv, reference_rows):
        """Converted (time_s, height_cm) values must match the independent fetch, sorted by time."""
        ref = pd.DataFrame(reference_rows, columns=["time_s", "height_cm"]).sort_values("time_s").to_numpy()
        got = agent_csv.sort_values("time_s")[["time_s", "height_cm"]].to_numpy()
        assert np.allclose(got, ref, atol=1e-6), "converted observation values do not match the reference"

    def test_sorted_by_time(self, agent_csv):
        """Rows must be sorted by ascending time_s."""
        ts = agent_csv["time_s"].to_numpy()
        assert np.all(np.diff(ts) >= 0), "observations.csv must be sorted by ascending time_s"
