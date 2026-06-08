"""Tests for milestone 1 (Query Earthquake Catalog). Run alone with: pytest tests/test_m1.py

These tests seed deterministic SQLite catalogs, run the agent's compiled
`/app/quake query` against them, and check that the CSV output matches an
independent reimplementation of the filter (see _reference.py) in row set,
ordering and numeric formatting, and that invalid filters exit with status 2.
"""

import csv
import os
import re
import subprocess

import pytest

import _reference
import _seed

BIN = os.environ.get("QUAKE_BIN", "/app/quake")


@pytest.fixture(scope="module")
def catalog(tmp_path_factory):
    path = tmp_path_factory.mktemp("cat") / "catalog.db"
    n = _seed.seed_catalog(str(path))
    assert n > 1000, "seed produced too few events"
    return str(path)


def run_query(catalog, out, *args):
    cmd = [BIN, "query", "--db", catalog, "--out", str(out), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def read_csv(path):
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    return header, rows


HEADER = ["id", "time", "latitude", "longitude", "depth_km", "magnitude", "region"]


class TestMilestone1:
    """Milestone 1: SQL-filtered event export to deterministic CSV."""

    @pytest.mark.parametrize("filt,args", [
        ({}, []),
        ({"region": "SanAndreas"}, ["--region", "SanAndreas"]),
        ({"region": "Cascadia", "mag_min": 3.0}, ["--region", "Cascadia", "--mag-min", "3.0"]),
        ({"mag_min": 2.5, "mag_max": 4.0}, ["--mag-min", "2.5", "--mag-max", "4.0"]),
        ({"lat_min": 40.0, "lat_max": 45.0, "lon_min": -126.0, "lon_max": -123.0},
         ["--lat-min", "40", "--lat-max", "45", "--lon-min", "-126", "--lon-max", "-123"]),
        ({"start": "2010-01-01T00:00:00Z", "end": "2012-12-31T23:59:59Z"},
         ["--start", "2010-01-01T00:00:00Z", "--end", "2012-12-31T23:59:59Z"]),
        ({"region": "Aleutian", "depth_min": 20.0, "depth_max": 80.0},
         ["--region", "Aleutian", "--depth-min", "20", "--depth-max", "80"]),
    ])
    def test_filtered_rows_match_reference(self, catalog, tmp_path, filt, args):
        """Each filter combination must yield exactly the reference row set, in order."""
        out = tmp_path / "q.csv"
        res = run_query(catalog, out, *args)
        assert res.returncode == 0, f"query failed: {res.stderr}"
        header, rows = read_csv(out)
        assert header == HEADER, f"wrong header: {header}"
        expected = _reference.query_events(catalog, filt)
        got_ids = [int(r[0]) for r in rows]
        exp_ids = [e["id"] for e in expected]
        assert got_ids == exp_ids, "row set or ordering differs from the SQL reference"

    def test_ordering_is_time_then_id(self, catalog, tmp_path):
        """Rows must be ordered by time ascending, breaking ties by id ascending."""
        out = tmp_path / "q.csv"
        assert run_query(catalog, out, "--region", "SanAndreas").returncode == 0
        _h, rows = read_csv(out)
        keys = [(r[1], int(r[0])) for r in rows]
        assert keys == sorted(keys), "rows are not ordered by (time, id)"

    def test_numeric_formatting(self, catalog, tmp_path):
        """latitude/longitude 4dp, depth_km 2dp, magnitude 1dp, exact values."""
        out = tmp_path / "q.csv"
        assert run_query(catalog, out, "--region", "Cascadia", "--mag-min", "4.0").returncode == 0
        _h, rows = read_csv(out)
        expected = {e["id"]: e for e in _reference.query_events(
            catalog, {"region": "Cascadia", "mag_min": 4.0})}
        assert rows, "expected some high-magnitude events"
        for r in rows:
            assert re.fullmatch(r"-?\d+\.\d{4}", r[2]), f"latitude not 4dp: {r[2]}"
            assert re.fullmatch(r"-?\d+\.\d{4}", r[3]), f"longitude not 4dp: {r[3]}"
            assert re.fullmatch(r"-?\d+\.\d{2}", r[4]), f"depth not 2dp: {r[4]}"
            assert re.fullmatch(r"-?\d+\.\d", r[5]), f"magnitude not 1dp: {r[5]}"
            e = expected[int(r[0])]
            assert abs(float(r[2]) - e["latitude"]) < 5e-5
            assert abs(float(r[3]) - e["longitude"]) < 5e-5
            assert abs(float(r[4]) - e["depth_km"]) < 5e-3
            assert abs(float(r[5]) - e["magnitude"]) < 5e-2
            assert r[6] == e["region"]

    def test_combined_region_and_box(self, catalog, tmp_path):
        """A named region AND a bounding box must both be applied (intersection)."""
        out = tmp_path / "q.csv"
        args = ["--region", "Cascadia", "--lat-min", "42", "--lat-max", "45"]
        assert run_query(catalog, out, *args).returncode == 0
        _h, rows = read_csv(out)
        exp = _reference.query_events(catalog, {"region": "Cascadia", "lat_min": 42.0, "lat_max": 45.0})
        assert [int(r[0]) for r in rows] == [e["id"] for e in exp]
        assert all(r[6] == "Cascadia" and 42.0 <= float(r[2]) <= 45.0 for r in rows)

    def test_empty_result_is_header_only(self, catalog, tmp_path):
        """A valid filter matching nothing writes only the header and exits 0."""
        out = tmp_path / "q.csv"
        res = run_query(catalog, out, "--region", "Atlantis")
        assert res.returncode == 0
        header, rows = read_csv(out)
        assert header == HEADER and rows == []

    @pytest.mark.parametrize("args", [
        ["--lat-min", "50", "--lat-max", "10"],
        ["--lon-min", "10", "--lon-max", "-10"],
        ["--mag-min", "6", "--mag-max", "2"],
        ["--depth-min", "30", "--depth-max", "5"],
        ["--start", "2015-01-01T00:00:00Z", "--end", "2010-01-01T00:00:00Z"],
        ["--lat-min", "200"],
        ["--lon-min", "-999"],
        ["--mag-min", "abc"],
        ["--bogus", "1"],
        ["--region"],  # missing value
    ])
    def test_invalid_filters_exit_2(self, catalog, tmp_path, args):
        """Invalid invocations must exit with status code 2."""
        out = tmp_path / "q.csv"
        res = run_query(catalog, out, *args)
        assert res.returncode == 2, f"expected exit 2 for {args}, got {res.returncode}"

    def test_unknown_command_exits_2(self, catalog):
        """An unknown subcommand must exit 2."""
        res = subprocess.run([BIN, "frobnicate", "--db", catalog], capture_output=True, text=True)
        assert res.returncode == 2

    def test_default_db_path(self, tmp_path):
        """Omitting --db must default to the shipped /app/catalog.db."""
        out = tmp_path / "q.csv"
        res = subprocess.run([BIN, "query", "--out", str(out)], capture_output=True, text=True)
        assert res.returncode == 0, f"default-db query failed: {res.stderr}"
        header, rows = read_csv(out)
        assert header == HEADER
        assert len(rows) > 0, "/app/catalog.db should contain events"
