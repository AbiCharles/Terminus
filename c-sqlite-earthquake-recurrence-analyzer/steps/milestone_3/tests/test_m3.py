"""Tests for milestone 3 (Generate Deterministic Reports). Run alone with: pytest tests/test_m3.py

These tests seed deterministic catalogs, run the agent's `/app/quake report`, and
check the frequency-magnitude CSV and JSON summary against an independent
recomputation (see _reference.py): the FMD table, the shared statistics, and the
Poisson exceedance probabilities. They also confirm the outputs are byte-for-byte
reproducible and that the target order, window, and exit codes are honoured.
"""

import csv
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


def run_report(catalog, prefix, *args):
    return subprocess.run(
        [BIN, "report", "--db", catalog, "--out-prefix", str(prefix), *args],
        capture_output=True, text=True)


class TestMilestone3:
    """Milestone 3: deterministic FMD CSV + JSON summary with exceedance."""

    def test_fmd_matches_reference(self, catalog, tmp_path):
        pre = tmp_path / "rep"
        assert run_report(catalog, pre, "--region", "Cascadia").returncode == 0
        with open(f"{pre}_fmd.csv", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            rows = list(reader)
        assert header == ["magnitude", "count", "cumulative_count"]
        exp = _reference.fmd(catalog, {"region": "Cascadia"})
        assert len(rows) == len(exp), "FMD row count differs"
        for (gm, gc, gcc), (em, ec, ecc) in zip(rows, exp):
            assert abs(float(gm) - em) < 1e-9, f"bin {gm} != {em}"
            assert int(gc) == ec, f"count at {gm}: {gc} != {ec}"
            assert int(gcc) == ecc, f"cumulative at {gm}: {gcc} != {ecc}"
            assert re.fullmatch(r"-?\d+\.\d", gm), f"magnitude not 1dp: {gm}"

    def test_fmd_cumulative_is_monotone(self, catalog, tmp_path):
        pre = tmp_path / "rep"
        assert run_report(catalog, pre, "--region", "SanAndreas").returncode == 0
        with open(f"{pre}_fmd.csv", newline="") as fh:
            rows = list(csv.reader(fh))[1:]
        cums = [int(r[2]) for r in rows]
        assert cums == sorted(cums, reverse=True), "cumulative_count must be non-increasing"
        assert cums[0] == sum(int(r[1]) for r in rows), "top cumulative must equal total count"

    def test_summary_stats_match_reference(self, catalog, tmp_path):
        pre = tmp_path / "rep"
        assert run_report(catalog, pre, "--region", "Aleutian").returncode == 0
        got = json.loads(open(f"{pre}_summary.json").read())
        exp = _reference.compute_stats(catalog, {"region": "Aleutian"})
        assert abs(got["mc"] - exp["mc"]) < 1e-9
        assert got["n_total"] == exp["n_total"]
        assert got["n_above_mc"] == exp["n_above_mc"]
        assert abs(got["b_value"] - exp["b_value"]) <= 1e-3
        assert abs(got["a_value"] - exp["a_value"]) <= 2e-3
        assert abs(got["b_uncertainty"] - exp["b_uncertainty"]) <= 1e-3
        assert abs(got["catalog_years"] - exp["catalog_years"]) <= 1e-3

    def test_exceedance_matches_reference(self, catalog, tmp_path):
        pre = tmp_path / "rep"
        assert run_report(catalog, pre, "--region", "Cascadia",
                          "--targets", "4.5,5.5,6.5", "--window-years", "30").returncode == 0
        got = json.loads(open(f"{pre}_summary.json").read())
        assert abs(got["window_years"] - 30.0) < 1e-9
        exp_stats = _reference.compute_stats(catalog, {"region": "Cascadia"})
        exp_ex = _reference.exceedance(exp_stats, [4.5, 5.5, 6.5], 30.0)
        assert [o["magnitude"] for o in got["exceedance"]] == [4.5, 5.5, 6.5], "target order"
        for g, e in zip(got["exceedance"], exp_ex):
            assert abs(g["annual_rate"] - e["annual_rate"]) <= max(1e-6, 1e-3 * e["annual_rate"])
            assert abs(g["exceedance_probability"] - e["exceedance_probability"]) <= 1e-4

    def test_default_targets_and_window(self, catalog, tmp_path):
        pre = tmp_path / "rep"
        assert run_report(catalog, pre, "--region", "SanAndreas").returncode == 0
        got = json.loads(open(f"{pre}_summary.json").read())
        assert [o["magnitude"] for o in got["exceedance"]] == [5.0, 6.0, 7.0]
        assert abs(got["window_years"] - 50.0) < 1e-9

    def test_exceedance_number_formatting(self, catalog, tmp_path):
        pre = tmp_path / "rep"
        assert run_report(catalog, pre, "--region", "Cascadia").returncode == 0
        text = open(f"{pre}_summary.json").read()
        assert re.search(r'"annual_rate":\s*-?\d+\.\d{6}(?!\d)', text)
        assert re.search(r'"exceedance_probability":\s*-?\d+\.\d{6}(?!\d)', text)

    def test_outputs_are_deterministic(self, catalog, tmp_path):
        a, b = tmp_path / "a", tmp_path / "b"
        assert run_report(catalog, a, "--region", "Cascadia").returncode == 0
        assert run_report(catalog, b, "--region", "Cascadia").returncode == 0
        assert open(f"{a}_fmd.csv").read() == open(f"{b}_fmd.csv").read()
        assert open(f"{a}_summary.json").read() == open(f"{b}_summary.json").read()

    def test_insufficient_sample_exits_3(self, tmp_path):
        path = tmp_path / "tiny.db"
        _seed.seed_tiny(str(path))
        res = run_report(str(path), tmp_path / "rep")
        assert res.returncode == 3

    @pytest.mark.parametrize("args", [
        ["--targets", "5.0,abc"],
        ["--window-years", "0"],
        ["--window-years", "-5"],
        ["--lat-min", "200"],
    ])
    def test_invalid_exits_2(self, catalog, tmp_path, args):
        res = run_report(catalog, tmp_path / "rep", *args)
        assert res.returncode == 2

    def test_summary_is_valid_json_object(self, catalog, tmp_path):
        pre = tmp_path / "rep"
        assert run_report(catalog, pre, "--region", "Cascadia").returncode == 0
        assert isinstance(json.loads(open(f"{pre}_summary.json").read()), dict)
