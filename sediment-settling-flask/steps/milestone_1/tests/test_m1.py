"""Tests for milestone 1 (Extract Analysis Configuration).

Verifies /app/output/config.json combines the target experiment's per-experiment
fields and calibration constants (from /app/experiments.db) with the governing
analysis-method configuration extracted from /app/settling_standard.md — and that
the superseded / example / appendix distractor values were not used.
"""
import json
import pathlib

import pytest

import _reference as ref

CONFIG_PATH = pathlib.Path(ref.OUT_DIR) / "config.json"


@pytest.fixture(scope="module")
def config():
    assert CONFIG_PATH.exists(), f"{CONFIG_PATH} does not exist"
    with CONFIG_PATH.open() as fh:
        return json.load(fh)


class TestMilestone1:
    """Milestone 1: the extracted analysis configuration."""

    def test_config_schema(self, config):
        """config.json must be an object with experiment_id, experiment and method."""
        assert isinstance(config, dict)
        assert config["experiment_id"] == ref.TARGET_ID
        assert isinstance(config["experiment"], dict)
        assert isinstance(config["method"], dict)

    def test_experiment_matches_database(self, config):
        """The experiment block must match an independent DB query for experiment 7."""
        expected = ref.experiment(ref.TARGET_ID)
        exp = config["experiment"]
        assert exp["label"] == expected["label"]
        for key in ("column_height_cm", "fluid_viscosity_pa_s", "fluid_density_kg_m3",
                    "particle_density_kg_m3", "temperature_c", "raw_scale", "raw_offset"):
            assert key in exp, f"missing experiment field {key}"
            assert abs(float(exp[key]) - float(expected[key])) < 1e-9, (
                f"{key}: {exp[key]} != {expected[key]}"
            )

    def test_method_matches_governing_standard(self, config):
        """The method block must hold the governing Revision-C values from §8/§9."""
        method = config["method"]
        for key, want in ref.CORRECT_METHOD.items():
            assert key in method, f"missing method field {key}"
            if isinstance(want, str):
                assert method[key] == want, f"{key}: {method[key]} != {want}"
            else:
                assert abs(float(method[key]) - float(want)) < 1e-9, (
                    f"{key}: {method[key]} != {want}"
                )

    def test_method_rejects_distractors(self, config):
        """No method field may carry a superseded / example / appendix distractor value."""
        method = config["method"]
        for key, bad in ref.DISTRACTOR_METHOD.items():
            if isinstance(bad, str):
                assert method[key] != bad, f"{key} used superseded value {bad}"
            else:
                assert abs(float(method[key]) - float(bad)) > 1e-9, (
                    f"{key} used non-governing value {bad}"
                )
