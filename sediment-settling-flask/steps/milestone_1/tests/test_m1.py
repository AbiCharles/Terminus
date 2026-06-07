"""Tests for milestone 1 (Query Experiment Metadata).

Verifies /app/output/metadata.json holds the target experiment's metadata and
calibration constants, matching an independent query of /app/experiments.db.
"""
import json
import pathlib

import pytest

import _reference as ref

META_PATH = pathlib.Path(ref.OUT_DIR) / "metadata.json"


@pytest.fixture(scope="module")
def metadata():
    assert META_PATH.exists(), f"{META_PATH} does not exist"
    with META_PATH.open() as fh:
        return json.load(fh)


class TestMilestone1:
    """Milestone 1: experiment metadata extracted from SQLite."""

    def test_metadata_is_json_object(self, metadata):
        """metadata.json must parse as a JSON object."""
        assert isinstance(metadata, dict)

    def test_metadata_matches_database(self, metadata):
        """Every metadata field must match an independent DB query for experiment 7."""
        expected = ref.metadata(ref.TARGET_ID)
        assert metadata["experiment_id"] == expected["experiment_id"]
        assert metadata["label"] == expected["label"]
        for key in ("column_height_cm", "fluid_viscosity_pa_s", "fluid_density_kg_m3",
                    "particle_density_kg_m3", "temperature_c", "raw_scale", "raw_offset"):
            assert key in metadata, f"missing field {key}"
            assert abs(float(metadata[key]) - float(expected[key])) < 1e-9, (
                f"{key}: {metadata[key]} != {expected[key]}"
            )
