"""Tests for milestone 2 (Decluster the Catalog). Run alone with: pytest tests/test_m2.py

These tests seed deterministic catalogs that contain genuine aftershock
sequences, run the agent's `/app/quake decluster`, and check the surviving
mainshock CSV against an independent Gardner-Knopoff reimplementation
(see _reference.py): the exact mainshock set, ordering and numeric formatting.
A correct match requires the specified windowing, haversine distance, julianday
time separation and decreasing-magnitude processing order — an approximate or
differently-ordered declustering falls outside the exact set.
"""

import csv
import os
import subprocess

import pytest

import _reference
import _seed

BIN = os.environ.get("QUAKE_BIN", "/app/quake")
HEADER = ["id", "time", "latitude", "longitude", "depth_km", "magnitude", "region"]


@pytest.fixture(scope="module")
def catalog(tmp_path_factory):
    path = tmp_path_factory.mktemp("cat") / "catalog.db"
    n = _seed.seed_catalog(str(path))
    assert n > 1000, "seed produced too few events"
    return str(path)


def run_decluster(catalog, out, *args):
    return subprocess.run(
        [BIN, "decluster", "--db", catalog, "--out", str(out), *args],
        capture_output=True, text=True)


def read_csv(path):
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        return next(reader), list(reader)


class TestMilestone2:
    """Milestone 2: Gardner-Knopoff declustering to a mainshock catalog."""

    @pytest.mark.parametrize("filt,args", [
        ({}, []),
        ({"region": "Cascadia"}, ["--region", "Cascadia"]),
        ({"region": "SanAndreas"}, ["--region", "SanAndreas"]),
        ({"region": "Aleutian"}, ["--region", "Aleutian"]),
        ({"mag_min": 3.0}, ["--mag-min", "3.0"]),
        ({"region": "Cascadia", "depth_max": 30.0}, ["--region", "Cascadia", "--depth-max", "30"]),
    ])
    def test_mainshocks_match_reference(self, catalog, tmp_path, filt, args):
        """The surviving mainshock set and order must equal the reference exactly."""
        out = tmp_path / "d.csv"
        res = run_decluster(catalog, out, *args)
        assert res.returncode == 0, f"decluster failed: {res.stderr}"
        header, rows = read_csv(out)
        assert header == HEADER, f"wrong header: {header}"
        got_ids = [int(r[0]) for r in rows]
        exp_ids = [e["id"] for e in _reference.decluster(catalog, filt)]
        assert got_ids == exp_ids, "mainshock set or ordering differs from the Gardner-Knopoff reference"

    def test_actually_removes_aftershocks(self, catalog, tmp_path):
        """Declustering the clustered catalog must remove a non-trivial fraction."""
        out = tmp_path / "d.csv"
        assert run_decluster(catalog, out).returncode == 0
        _h, mains = read_csv(out)
        full = _reference.query_events(catalog, {})
        assert len(mains) < len(full), "no events were removed — declustering is a no-op"
        removed_frac = 1.0 - len(mains) / len(full)
        assert removed_frac > 0.1, f"only {removed_frac:.0%} removed; expected a real aftershock population"

    def test_mainshocks_are_a_subset(self, catalog, tmp_path):
        """Every surviving id must be a real event from the filtered catalog."""
        out = tmp_path / "d.csv"
        assert run_decluster(catalog, out, "--region", "Aleutian").returncode == 0
        _h, mains = read_csv(out)
        got = {int(r[0]) for r in mains}
        full = {e["id"] for e in _reference.query_events(catalog, {"region": "Aleutian"})}
        assert got <= full, "decluster emitted ids absent from the filtered catalog"

    def test_largest_event_always_survives(self, catalog, tmp_path):
        """The maximum-magnitude event can never be removed as an aftershock."""
        out = tmp_path / "d.csv"
        assert run_decluster(catalog, out, "--region", "Cascadia").returncode == 0
        _h, mains = read_csv(out)
        full = _reference.query_events(catalog, {"region": "Cascadia"})
        biggest = max(full, key=lambda e: e["magnitude"])
        assert biggest["id"] in {int(r[0]) for r in mains}, "the largest event was wrongly removed"

    def test_ordering_is_time_then_id(self, catalog, tmp_path):
        """Mainshocks must be ordered by time ascending, then id ascending."""
        out = tmp_path / "d.csv"
        assert run_decluster(catalog, out).returncode == 0
        _h, rows = read_csv(out)
        keyed = [(r[1], int(r[0])) for r in rows]
        assert keyed == sorted(keyed), "rows are not ordered by (time, id)"

    def test_numeric_formatting(self, catalog, tmp_path):
        """lat/lon four decimals, depth two, magnitude one; id/time/region verbatim."""
        out = tmp_path / "d.csv"
        assert run_decluster(catalog, out, "--region", "Cascadia").returncode == 0
        _h, rows = read_csv(out)
        assert rows, "expected at least one mainshock"
        for r in rows[:200]:
            assert len(r[2].split(".")[1]) == 4, f"latitude not 4dp: {r[2]}"
            assert len(r[3].split(".")[1]) == 4, f"longitude not 4dp: {r[3]}"
            assert len(r[4].split(".")[1]) == 2, f"depth not 2dp: {r[4]}"
            assert len(r[5].split(".")[1]) == 1, f"magnitude not 1dp: {r[5]}"

    def test_empty_result_is_header_only(self, catalog, tmp_path):
        """A valid filter matching nothing writes the header alone and exits 0."""
        out = tmp_path / "d.csv"
        res = run_decluster(catalog, out, "--region", "Cascadia", "--mag-min", "9.5")
        assert res.returncode == 0, f"expected success, got {res.returncode}: {res.stderr}"
        header, rows = read_csv(out)
        assert header == HEADER and rows == [], "empty decluster must be header-only"

    @pytest.mark.parametrize("args", [
        ["--lat-min", "200"],
        ["--lon-max", "999"],
        ["--lat-min", "10", "--lat-max", "5"],
        ["--mag-min", "abc"],
        ["--bogus"],
        ["--region"],
        ["--start", "2020-01-01T00:00:00Z", "--end", "2019-01-01T00:00:00Z"],
    ])
    def test_invalid_filters_exit_2(self, catalog, tmp_path, args):
        """Invalid invocations must exit 2 before doing any declustering."""
        out = tmp_path / "d.csv"
        res = run_decluster(catalog, out, *args)
        assert res.returncode == 2, f"expected exit 2 for {args}, got {res.returncode}"
