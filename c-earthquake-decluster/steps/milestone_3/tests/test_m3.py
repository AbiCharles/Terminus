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
        # All required summary keys must be present and correct (not just the stats subset).
        assert got["completeness_method"] == "goodness_of_fit"
        assert abs(got["gft_confidence"] - 90.0) < 1e-9
        assert abs(got["delta_m"] - 0.1) < 1e-9
        assert abs(got["magnitude_range"]["min"] - exp["magnitude_range"]["min"]) < 1e-9
        assert abs(got["magnitude_range"]["max"] - exp["magnitude_range"]["max"]) < 1e-9

    def test_per_region_matches_reference(self, catalog, tmp_path):
        """The per_region array must hold a correct G-R fit per region, in name order."""
        pre = tmp_path / "rep"
        assert run_report(catalog, pre).returncode == 0
        got = json.loads(open(f"{pre}_summary.json").read())
        exp = _reference.per_region(catalog, {})
        assert "per_region" in got, "summary is missing the per_region array"
        gpr = got["per_region"]
        assert [b["region"] for b in gpr] == [e["region"] for e in exp], \
            "per_region regions differ from the reference (set or ordering)"
        assert len(gpr) >= 2, "expected a per-region breakdown over multiple regions"
        for g, e in zip(gpr, exp):
            assert g["n_total"] == e["n_total"], f"{e['region']} n_total"
            assert g["n_above_mc"] == e["n_above_mc"], f"{e['region']} n_above_mc"
            assert abs(g["mc"] - e["mc"]) < 1e-9, f"{e['region']} mc"
            assert abs(g["b_value"] - e["b_value"]) <= 1e-3, f"{e['region']} b_value"
            assert abs(g["b_uncertainty"] - e["b_uncertainty"]) <= 1e-3, f"{e['region']} b_uncertainty"
            assert abs(g["a_value"] - e["a_value"]) <= 2e-3, f"{e['region']} a_value"

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

    def test_summary_number_formatting(self, catalog, tmp_path):
        """All numeric summary fields must be bare JSON numbers with the exact stated
        decimals incl. trailing zeros (4dp for b/sigma/a/years, 1dp for mc/range) —
        in the top-level stats and in every per_region block."""
        pre = tmp_path / "rep"
        assert run_report(catalog, pre).returncode == 0
        text = open(f"{pre}_summary.json").read()
        for key in ("b_value", "b_uncertainty", "a_value", "catalog_years"):
            assert re.search(rf'"{key}":\s*-?\d+\.\d{{4}}(?!\d)', text), f"{key} not 4-decimal bare number"
        assert re.search(r'"mc":\s*-?\d+\.\d(?!\d)', text), "mc not 1-decimal bare number"
        assert re.search(r'"min":\s*-?\d+\.\d(?!\d)', text), "magnitude_range.min not 1-decimal"
        # per_region blocks must use the same bare-number formatting
        pr = json.loads(text)["per_region"]
        assert pr, "expected per_region blocks"
        for blk in re.findall(r'\{"region":.*?\}', text):
            assert re.search(r'"b_value":\s*-?\d+\.\d{4}(?!\d)', blk), f"per_region b_value not 4dp: {blk}"
            assert re.search(r'"mc":\s*-?\d+\.\d(?!\d)', blk), f"per_region mc not 1dp: {blk}"
            # ensure numeric (not string) — json parse already succeeded above
        for blk in pr:
            assert isinstance(blk["b_value"], (int, float)), "per_region b_value must be a JSON number"

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
