"""Tests for milestone 2 (Query Buoy Observations). Run alone with: pytest tests/test_m2.py

These tests verify that, for every calibrated buoy (active status, included sensor
type), /app/artifacts/<buoy_id>/clean.csv contains the cleaned residual series the
binding rules imply — exclusion windows dropped, unit conversion applied, elapsed
days computed from the mission epoch, residual = converted - reference — checked
against an independent recomputation straight from the SQLite store (_reference.py).
Buoys that are retired or carry a non-included sensor type must produce no output.
"""

import csv
import sqlite3
from pathlib import Path

import numpy as np
import pytest

import _reference

ARTIFACTS = Path("/app/artifacts")
EXPECTED_HEADER = ["timestamp", "t_days", "converted_value", "reference_value", "residual"]


@pytest.fixture(scope="module")
def included():
    ids = _reference.included_buoys()
    assert ids, "no calibrated buoys found"
    return ids


def read_clean(path):
    with path.open(newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [r for r in reader if r]
    return header, rows


class TestMilestone2:
    """Milestone 2: per-buoy cleaned residual series derived from the database."""

    def test_each_included_buoy_has_clean_csv(self, included):
        """Every calibrated buoy must have a clean.csv with the specified header."""
        for buoy in included:
            path = ARTIFACTS / buoy / "clean.csv"
            assert path.exists(), f"{buoy} missing clean.csv"
            header, _ = read_clean(path)
            assert header == EXPECTED_HEADER, f"{buoy} wrong header: {header}"

    def test_rows_match_reference(self, included):
        """Timestamps, elapsed days, converted/reference values and residuals must match."""
        for buoy in included:
            _header, rows = read_clean(ARTIFACTS / buoy / "clean.csv")
            ref = _reference.clean_series(buoy)
            assert len(rows) == len(ref["timestamp"]), f"{buoy} row count differs"
            assert [r[0] for r in rows] == ref["timestamp"], f"{buoy} timestamps differ/unordered"
            for col, key in enumerate(["t_days", "converted_value", "reference_value", "residual"], start=1):
                got = np.array([float(r[col]) for r in rows], dtype=np.float64)
                exp = np.array(ref[key], dtype=np.float64)
                assert np.allclose(got, exp, rtol=1e-6, atol=1e-9), f"{buoy} {key} differs from reference"

    def test_exclusion_windows_applied(self, included):
        """No admitted timestamp may fall inside an exclusion window for that buoy."""
        for buoy in included:
            _header, rows = read_clean(ARTIFACTS / buoy / "clean.csv")
            for r in rows:
                ts_dt = _reference._parse(r[0])
                assert not _reference._is_excluded(buoy, ts_dt), (
                    f"{buoy} admitted an excluded timestamp {r[0]}"
                )

    def test_non_calibrated_buoys_have_no_output(self, included):
        """Retired buoys and non-included sensor types must produce no artifact directory."""
        con = sqlite3.connect(_reference.DB_PATH)
        try:
            all_ids = [r[0] for r in con.execute("SELECT buoy_id FROM buoys").fetchall()]
        finally:
            con.close()
        excluded = set(all_ids) - set(included)
        assert excluded, "expected at least one non-calibrated buoy as a distractor"
        for buoy in excluded:
            assert not (ARTIFACTS / buoy).exists(), f"{buoy} must not have an output directory"
