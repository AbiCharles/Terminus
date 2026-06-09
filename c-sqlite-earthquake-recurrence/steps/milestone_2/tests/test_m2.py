"""Tests for milestone 2 (Compute Seismic Statistics). Run alone with: pytest tests/test_m2.py

These tests seed deterministic catalogs, run the agent's `/app/quake stats`, and
check the JSON against an independent recomputation (see _reference.py): the
goodness-of-fit Mc must match exactly, and the Aki-Utsu b-value, Shi & Bolt
uncertainty and a-value within tolerance. A correct match requires implementing
the specified GFT scan and binning, not a different completeness heuristic.
Insufficient samples must exit 3 and invalid filters exit 2.
"""

import json
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
    _seed.seed_catalog(str(path))
    return str(path)


def run_stats(catalog, out, *args):
    return subprocess.run(
        [BIN, "stats", "--db", catalog, "--out", str(out), *args],
        capture_output=True, text=True)


REQUIRED_KEYS = {
    "completeness_method", "gft_confidence", "delta_m", "n_total", "n_above_mc",
    "mc", "b_value", "b_uncertainty", "a_value", "catalog_years", "magnitude_range",
}


class TestMilestone2:
    """Milestone 2: completeness, b-value and a-value from the filtered catalog."""

    @pytest.mark.parametrize("filt,args", [
        ({}, []),
        ({"region": "Cascadia"}, ["--region", "Cascadia"]),
        ({"region": "SanAndreas"}, ["--region", "SanAndreas"]),
        ({"region": "Aleutian"}, ["--region", "Aleutian"]),
    ])
    def test_stats_match_reference(self, catalog, tmp_path, filt, args):
        out = tmp_path / "s.json"
        res = run_stats(catalog, out, *args)
        assert res.returncode == 0, f"stats failed: {res.stderr}"
        got = json.loads(out.read_text())
        assert REQUIRED_KEYS.issubset(got), f"missing keys: {REQUIRED_KEYS - set(got)}"
        exp = _reference.compute_stats(catalog, filt)
        # Completeness must match exactly (the GFT lever).
        assert abs(got["mc"] - exp["mc"]) < 1e-9, f"mc {got['mc']} != reference {exp['mc']}"
        assert got["n_total"] == exp["n_total"]
        assert got["n_above_mc"] == exp["n_above_mc"]
        assert abs(got["b_value"] - exp["b_value"]) <= 1e-3, "b_value off"
        assert abs(got["a_value"] - exp["a_value"]) <= 2e-3, "a_value off"
        assert abs(got["b_uncertainty"] - exp["b_uncertainty"]) <= 1e-3, "b_uncertainty off"
        assert abs(got["catalog_years"] - exp["catalog_years"]) <= 1e-3, "catalog_years off"
        assert abs(got["magnitude_range"]["min"] - exp["magnitude_range"]["min"]) < 1e-9
        assert abs(got["magnitude_range"]["max"] - exp["magnitude_range"]["max"]) < 1e-9

    def test_stdout_when_no_out_flag(self, catalog):
        """With --out omitted, the JSON summary must be written to standard output."""
        res = subprocess.run([BIN, "stats", "--db", catalog], capture_output=True, text=True)
        assert res.returncode == 0, f"stats (stdout) failed: {res.stderr}"
        got = json.loads(res.stdout)
        assert REQUIRED_KEYS.issubset(got), f"missing keys: {REQUIRED_KEYS - set(got)}"
        exp = _reference.compute_stats(catalog, {})
        assert abs(got["mc"] - exp["mc"]) < 1e-9
        assert got["n_total"] == exp["n_total"]

    def test_method_constants(self, catalog, tmp_path):
        out = tmp_path / "s.json"
        assert run_stats(catalog, out).returncode == 0
        got = json.loads(out.read_text())
        assert got["completeness_method"] == "goodness_of_fit"
        assert abs(got["gft_confidence"] - 90.0) < 1e-9
        assert abs(got["delta_m"] - 0.1) < 1e-9

    def test_json_numeric_formatting(self, catalog, tmp_path):
        """mc/range one decimal; b_value, b_uncertainty, a_value, catalog_years four decimals."""
        out = tmp_path / "s.json"
        assert run_stats(catalog, out, "--region", "Cascadia").returncode == 0
        text = out.read_text()
        assert re.search(r'"mc":\s*-?\d+\.\d(?!\d)', text), "mc must have one decimal"
        for key in ("b_value", "b_uncertainty", "a_value", "catalog_years"):
            assert re.search(rf'"{key}":\s*-?\d+\.\d{{4}}(?!\d)', text), f"{key} must have four decimals"

    def test_b_value_is_plausible(self, catalog, tmp_path):
        """Sanity: a recovered b-value should sit in a geophysically reasonable band."""
        out = tmp_path / "s.json"
        assert run_stats(catalog, out).returncode == 0
        b = json.loads(out.read_text())["b_value"]
        assert 0.5 < b < 1.5, f"b_value {b} implausible"

    def test_insufficient_sample_exits_3(self, tmp_path):
        path = tmp_path / "tiny.db"
        _seed.seed_tiny(str(path))
        out = tmp_path / "s.json"
        res = run_stats(str(path), out)
        assert res.returncode == 3, f"expected exit 3, got {res.returncode}"

    def test_no_match_exits_3(self, catalog, tmp_path):
        out = tmp_path / "s.json"
        res = run_stats(catalog, out, "--region", "Atlantis")
        assert res.returncode == 3

    @pytest.mark.parametrize("args", [
        ["--mag-min", "6", "--mag-max", "2"],
        ["--lat-min", "abc"],
        ["--nope", "1"],
    ])
    def test_invalid_exits_2(self, catalog, tmp_path, args):
        out = tmp_path / "s.json"
        res = run_stats(catalog, out, *args)
        assert res.returncode == 2
