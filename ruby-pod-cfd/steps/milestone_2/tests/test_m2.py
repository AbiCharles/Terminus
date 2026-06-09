"""Milestone 2: POD via covariance eigenanalysis (modal energy + cumulative variance)."""
import glob
import json
import os
import re

import numpy as np

import _reference as R

OUTPUT = "/app/output"


class TestMilestone2:
    def test_milestone_1_still_holds(self):
        for eid in R.fixture_ids():
            assert os.path.isfile(os.path.join(OUTPUT, eid, "snapshots_meta.json")), f"{eid}: M1 output missing"

    def test_modal_energy_matches_reference(self):
        for eid in R.fixture_ids():
            X, _ = R.assemble(eid)
            _, frac, cum = R.pod(X)
            me = json.load(open(os.path.join(OUTPUT, eid, "modal_energy.json")))
            modes = sorted(me["modes"], key=lambda m: m["mode_index"])
            got_frac = np.array([m["energy_fraction"] for m in modes])
            got_cum = np.array([m["cumulative_fraction"] for m in modes])
            assert len(got_frac) == len(frac), f"{eid}: wrong number of modes"
            assert np.allclose(got_frac, frac, rtol=1e-3, atol=1e-7), f"{eid}: energy fractions"
            assert np.allclose(got_cum, cum, rtol=1e-3, atol=1e-7), f"{eid}: cumulative variance"

    def test_modal_energy_csv_present_and_consistent(self):
        for eid in R.fixture_ids():
            path = os.path.join(OUTPUT, eid, "modal_energy.csv")
            assert os.path.isfile(path), f"{eid}: modal_energy.csv missing"
            header = open(path).readline().strip().split(",")
            assert header == ["mode_index", "eigenvalue", "energy_fraction", "cumulative_fraction"], \
                f"{eid}: unexpected CSV header {header}"

    def test_eigenanalysis_implemented_from_scratch(self):
        src = ""
        for p in sorted(set(glob.glob("/app/*.rb") + glob.glob("/app/**/*.rb", recursive=True))):
            src += open(p).read() + "\n"
        forbidden = [r'require\s+["\']matrix["\']', r'numo', r'nmatrix', r'\.eigensystem', r'\.eigenvalues']
        for pat in forbidden:
            assert not re.search(pat, src), \
                f"linear-algebra library usage matching /{pat}/ is not allowed — implement the eigenanalysis from scratch"
