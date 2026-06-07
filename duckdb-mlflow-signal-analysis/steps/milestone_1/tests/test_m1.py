"""Tests for milestone 1 (Query Experiment Database). Run alone with: pytest tests/test_m1.py

These tests verify that `query` wrote, for every valid experiment in the DuckDB
store, a /app/artifacts/<id>/measurements.csv whose rows match the database (read
back independently via SQL in _reference.py) and a metadata.json with the correct
sample rate and sample count, and that non-valid experiments produced no output.
"""

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import _reference

ARTIFACTS = Path("/app/artifacts")


@pytest.fixture(scope="module")
def valid_ids():
    ids = _reference.valid_experiment_ids()
    assert ids, "no valid experiments found in the database"
    return ids


def read_csv_columns(path):
    with path.open(newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [(int(r[0]), float(r[1])) for r in reader if r]
    indices = [r[0] for r in rows]
    signal = np.array([r[1] for r in rows], dtype=np.float64)
    return header, indices, signal


class TestMilestone1:
    """Milestone 1: per-experiment sample CSVs and metadata extracted via SQL."""

    def test_artifacts_directory_exists(self):
        """The /app/artifacts output directory must have been created."""
        assert ARTIFACTS.is_dir(), "/app/artifacts directory was not created"

    def test_each_valid_experiment_has_outputs(self, valid_ids):
        """Every valid experiment must have a measurements.csv and metadata.json."""
        for exp in valid_ids:
            assert (ARTIFACTS / exp / "measurements.csv").exists(), f"{exp} missing measurements.csv"
            assert (ARTIFACTS / exp / "metadata.json").exists(), f"{exp} missing metadata.json"

    def test_csv_header_and_order(self, valid_ids):
        """measurements.csv must have header sample_index,signal ordered by sample_index."""
        for exp in valid_ids:
            header, indices, _signal = read_csv_columns(ARTIFACTS / exp / "measurements.csv")
            assert header == ["sample_index", "signal"], f"{exp} has wrong CSV header: {header}"
            _sr, n_samples, _status = _reference.experiment_metadata(exp)
            assert indices == list(range(n_samples)), f"{exp} sample_index column is wrong/unordered"

    def test_csv_signal_matches_database(self, valid_ids):
        """The signal column must match the values stored in the database exactly."""
        for exp in valid_ids:
            _header, _indices, signal = read_csv_columns(ARTIFACTS / exp / "measurements.csv")
            expected = _reference.load_signal(exp)
            assert signal.shape == expected.shape, f"{exp} row count differs from database"
            assert np.allclose(signal, expected, rtol=1e-9, atol=1e-9), (
                f"{exp} signal values do not match the database"
            )

    def test_metadata_contents(self, valid_ids):
        """metadata.json must report the experiment id, sample rate and sample count."""
        for exp in valid_ids:
            meta = json.loads((ARTIFACTS / exp / "metadata.json").read_text())
            sample_rate, n_samples, _status = _reference.experiment_metadata(exp)
            assert meta["experiment_id"] == exp
            assert float(meta["sample_rate_hz"]) == pytest.approx(sample_rate)
            assert int(meta["n_samples"]) == n_samples

    def test_non_valid_experiments_skipped(self):
        """Experiments whose status is not 'valid' must not produce any output."""
        nonvalid = _reference.nonvalid_experiment_ids()
        assert nonvalid, "expected at least one non-valid experiment in the database"
        for exp in nonvalid:
            assert not (ARTIFACTS / exp).exists(), (
                f"{exp} is not valid and must not have an output directory"
            )
