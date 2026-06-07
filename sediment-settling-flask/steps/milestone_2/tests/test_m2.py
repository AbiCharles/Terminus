"""Tests for milestone 2 (Retrieve Settling Observations).

Verifies /app/output/observations.csv contains every observation (all API pages),
converted to physical units via the sensor calibration, sorted by time.
"""
import pathlib

import numpy as np
import pandas as pd
import pytest

import _reference as ref

OBS_PATH = pathlib.Path(ref.OUT_DIR) / "observations.csv"


@pytest.fixture(scope="module")
def observations():
    assert OBS_PATH.exists(), f"{OBS_PATH} does not exist"
    return pd.read_csv(OBS_PATH)


class TestMilestone2:
    """Milestone 2: observations fetched from the API and converted."""

    def test_metadata_persists(self):
        """The milestone 1 metadata.json must still exist (state persists)."""
        assert (pathlib.Path(ref.OUT_DIR) / "metadata.json").exists()

    def test_columns_and_count(self, observations):
        """observations.csv must have time_s,height_cm and one row per observation (all pages)."""
        assert list(observations.columns) == ["time_s", "height_cm"], "wrong columns/header"
        _, total = ref.converted_observations(ref.TARGET_ID)
        assert len(observations) == total, (
            f"expected {total} rows (every page), got {len(observations)}"
        )

    def test_sorted_by_time(self, observations):
        """Rows must be sorted by ascending time_s."""
        t = observations["time_s"].to_numpy()
        assert np.all(np.diff(t) >= 0), "observations not sorted by time_s"

    def test_values_match_reference(self, observations):
        """Converted (time_s, height_cm) values must match the independent fetch+convert."""
        expected, _ = ref.converted_observations(ref.TARGET_ID)
        exp = pd.DataFrame(expected, columns=["time_s", "height_cm"]).sort_values("time_s").reset_index(drop=True)
        got = observations.sort_values("time_s").reset_index(drop=True)
        assert np.abs(got["time_s"].to_numpy() - exp["time_s"].to_numpy()).max() < 1e-6, "time_s mismatch"
        assert np.abs(got["height_cm"].to_numpy() - exp["height_cm"].to_numpy()).max() < 1e-6, (
            "height_cm mismatch — check the raw->physical calibration conversion"
        )
