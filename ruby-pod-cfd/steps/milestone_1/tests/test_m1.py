"""Milestone 1: retrieve velocity-field frames from the API and assemble the matrix."""
import json
import os
import urllib.request

import numpy as np

import _reference as R

OUTPUT = "/app/output"


def _get(path):
    with urllib.request.urlopen(f"http://localhost:8000{path}", timeout=15) as r:
        return json.loads(r.read().decode())


class TestMilestone1:
    def test_each_fixture_has_meta(self):
        for eid in R.fixture_ids():
            assert os.path.isfile(os.path.join(OUTPUT, eid, "snapshots_meta.json")), \
                f"{eid}: missing output/{eid}/snapshots_meta.json"

    def test_assembled_matrix_matches_reference(self):
        for eid in R.fixture_ids():
            X, _ = R.assemble(eid)
            got = json.load(open(os.path.join(OUTPUT, eid, "snapshots_meta.json")))
            assert got["n_dofs"] == X.shape[0], f"{eid}: n_dofs"
            assert got["n_frames"] == X.shape[1], f"{eid}: n_frames (did you fetch every page?)"
            ref_norms = np.linalg.norm(X, axis=0)
            assert np.allclose(got["frame_l2_norms"], ref_norms, rtol=1e-6, atol=1e-6), \
                f"{eid}: frame L2 norms do not match (assembly order or values wrong)"
            ref_frob = float(np.linalg.norm(X))
            assert abs(got["frobenius_norm"] - ref_frob) <= 1e-6 * ref_frob, f"{eid}: frobenius_norm"

    def test_nonfixture_experiments_skipped(self):
        for eid in R.nonfixture_ids():
            assert not os.path.exists(os.path.join(OUTPUT, eid)), \
                f"{eid} is not a fixture and must not be analysed"

    def test_api_was_used(self):
        stats = _get("/_stats")
        assert stats["snapshot_requests"] > 0, "no snapshot pages were fetched from the API"
