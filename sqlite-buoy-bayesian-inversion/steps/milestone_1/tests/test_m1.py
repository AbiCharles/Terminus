"""Tests for milestone 1 (Extract Calibration Protocol). Run alone with: pytest tests/test_m1.py

Verifies /app/protocol.json encodes the binding Edition 3 criteria from the
governing sections of /app/mission_notebook.md — the mission epoch, inclusion
rule, per-sensor unit conversions, the drift changepoint, the per-sensor
three-parameter Gaussian priors (offset, drift, drift_change), and the exclusion
intervals — and that no superseded Edition 1/2 distractor values leaked in.
"""

import json
import math
from pathlib import Path

import pytest

import _reference

PROTOCOL_PATH = Path("/app/protocol.json")
EXPECTED = _reference.expected_protocol()


@pytest.fixture(scope="module")
def protocol():
    assert PROTOCOL_PATH.exists(), "/app/protocol.json does not exist — milestone 1 not completed"
    with PROTOCOL_PATH.open() as fh:
        return json.load(fh)


class TestMilestone1:
    """Milestone 1: the binding calibration protocol extracted into /app/protocol.json."""

    def test_is_json_object(self, protocol):
        """/app/protocol.json must parse as a JSON object."""
        assert isinstance(protocol, dict)

    def test_epoch_and_time_unit(self, protocol):
        """Mission epoch and time unit must be the binding values."""
        assert protocol["mission_epoch"] == EXPECTED["mission_epoch"]
        assert protocol["time_unit"] == "days"

    def test_epoch_not_superseded(self, protocol):
        """The superseded Edition 1/2 epochs must not be used."""
        assert not protocol["mission_epoch"].startswith("2022")
        assert not protocol["mission_epoch"].startswith("2023")

    def test_inclusion_rules(self, protocol):
        """Active status and the included sensor types must match the governing rule."""
        assert protocol["active_status"] == "active"
        assert protocol["active_status"] != "deployed"
        assert set(protocol["included_sensor_types"]) == {"temperature", "pressure"}
        assert "salinity" not in protocol["included_sensor_types"]

    def test_unit_conversions(self, protocol):
        """Per-sensor unit conversions must be the binding values, not superseded ones."""
        temp = protocol["sensors"]["temperature"]["unit_conversion"]
        press = protocol["sensors"]["pressure"]["unit_conversion"]
        assert math.isclose(temp, 0.0625, abs_tol=1e-12)
        assert math.isclose(press, 0.1, abs_tol=1e-12)
        assert not math.isclose(temp, 0.1, abs_tol=1e-9)
        assert not math.isclose(press, 0.25, abs_tol=1e-9)
        assert not math.isclose(press, 0.2, abs_tol=1e-9)

    def test_drift_changepoint(self, protocol):
        """The drift changepoint must be the binding servicing-end instant."""
        assert protocol["drift_changepoint"] == EXPECTED["drift_changepoint"]

    def test_priors(self, protocol):
        """Per-sensor Gaussian priors for offset, drift and drift_change must match the governing values."""
        for stype in ("temperature", "pressure"):
            got = protocol["sensors"][stype]["priors"]
            exp = EXPECTED["sensors"][stype]["priors"]
            for param in ("offset", "drift", "drift_change"):
                assert math.isclose(got[param]["mean"], exp[param]["mean"], abs_tol=1e-12), f"{stype}.{param}.mean"
                assert math.isclose(got[param]["std"], exp[param]["std"], abs_tol=1e-12), f"{stype}.{param}.std"

    def test_exclusion_intervals(self, protocol):
        """Exclusion windows must be exactly the binding set (no superseded windows)."""
        got = {(iv["buoy_id"], iv["start"], iv["end"]) for iv in protocol["exclusion_intervals"]}
        expected = {(iv["buoy_id"], iv["start"], iv["end"]) for iv in EXPECTED["exclusion_intervals"]}
        assert got == expected
        assert ("ALL", "2023-07-01T00:00:00Z", "2023-07-05T00:00:00Z") not in got
