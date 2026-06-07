"""Tests for milestone 1 (Query Experiment Metadata).
Run alone with: pytest tests/test_m1.py

Verifies /app/output/metadata.json joins experiment 1 with its sensor calibration,
matching an independent SQLite query (/app/spec.md §2).
"""

import json
import math
from pathlib import Path

import pytest

import _reference

META_PATH = Path("/app/output/metadata.json")


@pytest.fixture(scope="module")
def agent_meta():
    assert META_PATH.exists(), "/app/output/metadata.json does not exist — milestone 1 not completed"
    with META_PATH.open() as fh:
        return json.load(fh)


class TestMilestone1:
    """Milestone 1: experiment metadata joined with sensor calibration."""

    def test_required_keys(self, agent_meta):
        """metadata.json must contain exactly the specified keys."""
        assert set(agent_meta) == set(_reference.META_KEYS), (
            f"metadata.json keys mismatch: {set(agent_meta) ^ set(_reference.META_KEYS)}"
        )

    def test_values_match_reference(self, agent_meta):
        """Every field must match the independent experiments+sensors join for experiment 1."""
        expected = _reference.metadata()
        assert agent_meta["experiment_id"] == 1
        for key, exp in expected.items():
            got = agent_meta[key]
            if isinstance(exp, float):
                assert math.isclose(got, exp, rel_tol=0, abs_tol=1e-9), f"{key}: {got} != {exp}"
            else:
                assert got == exp, f"{key}: {got} != {exp}"
