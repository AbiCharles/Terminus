"""Milestone 3: mode selection for an energy threshold + reconstruction error."""
import json
import os
import subprocess
import tempfile


import _reference as R

OUTPUT = "/app/output"


class TestMilestone3:
    def test_milestone_2_still_holds(self):
        for eid in R.fixture_ids():
            assert os.path.isfile(os.path.join(OUTPUT, eid, "modal_energy.json")), f"{eid}: M2 output missing"

    def test_report_matches_reference_at_threshold(self):
        for eid in R.fixture_ids():
            X, _ = R.assemble(eid)
            eig, _, cum = R.pod(X)
            k = R.select_k(cum, R.THRESHOLD)
            rerr = R.recon_error(eig, k)
            rp = json.load(open(os.path.join(OUTPUT, eid, "report.json")))
            assert rp["n_selected_modes"] == k, f"{eid}: selected mode count at threshold {R.THRESHOLD}"
            assert rp["selected_mode_indices"] == list(range(k)), f"{eid}: selected_mode_indices"
            assert abs(rp["reconstruction_error"] - rerr) <= 1e-4, f"{eid}: reconstruction error"
            assert abs(rp["cumulative_at_selected"] - cum[k - 1]) <= 1e-4, f"{eid}: cumulative_at_selected"

    def test_report_csv_present_and_consistent(self):
        for eid in R.fixture_ids():
            path = os.path.join(OUTPUT, eid, "report.csv")
            assert os.path.isfile(path), f"{eid}: report.csv missing"
            header = open(path).readline().strip().split(",")
            assert header == ["experiment_id", "energy_threshold", "n_selected_modes", "reconstruction_error"], \
                f"{eid}: unexpected report.csv header {header}"

    def test_cli_recomputes_for_a_different_threshold(self):
        """Re-run the CLI at a different threshold; the report must track it (not be hardcoded)."""
        theta = 0.90
        with tempfile.TemporaryDirectory() as td:
            proc = subprocess.run(
                ["ruby", "/app/pod_cli.rb", "--base-url", "http://localhost:8000",
                 "--threshold", str(theta), "--output-dir", td],
                capture_output=True, text=True, timeout=180,
            )
            assert proc.returncode == 0, f"CLI failed at threshold {theta}: {proc.stderr}"
            for eid in R.fixture_ids():
                X, _ = R.assemble(eid)
                eig, _, cum = R.pod(X)
                k = R.select_k(cum, theta)
                rerr = R.recon_error(eig, k)
                rp = json.load(open(os.path.join(td, eid, "report.json")))
                assert rp["n_selected_modes"] == k, f"{eid}: k at theta={theta}"
                assert abs(rp["reconstruction_error"] - rerr) <= 1e-4, f"{eid}: recon at theta={theta}"
