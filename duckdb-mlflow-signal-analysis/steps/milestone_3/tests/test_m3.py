"""Tests for milestone 3 (Track MLflow Analysis Runs). Run alone with: pytest tests/test_m3.py

These tests open the agent's MLflow tracking store at /app/mlflow.db and verify that
every valid experiment has its own run in the signal-analysis experiment carrying the
required params, tags, metrics, and artifacts. The logged metrics are checked against
an independent recomputation from the database (see _reference.py) so fabricated or
mis-computed values are rejected.
"""

from pathlib import Path

import mlflow
import pytest
from mlflow.tracking import MlflowClient

import _reference

TRACKING_URI = "sqlite:////app/mlflow.db"
EXPERIMENT_NAME = "signal-analysis"


@pytest.fixture(scope="module")
def valid_ids():
    ids = _reference.valid_experiment_ids()
    assert ids, "no valid experiments found in the database"
    return ids


@pytest.fixture(scope="module")
def runs_by_experiment():
    assert Path("/app/mlflow.db").exists(), "/app/mlflow.db tracking store does not exist"
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    assert experiment is not None, f"MLflow experiment '{EXPERIMENT_NAME}' was not created"
    mapping = {}
    for run in client.search_runs([experiment.experiment_id]):
        key = run.data.tags.get("experiment_id") or run.data.tags.get("mlflow.runName")
        if key:
            mapping[key] = run
    return mapping


@pytest.fixture(scope="module")
def reference(valid_ids):
    return {exp: _reference.compute_analysis(exp) for exp in valid_ids}


class TestMilestone3:
    """Milestone 3: one MLflow run per valid experiment with analysis params/metrics/artifacts."""

    def test_every_valid_experiment_has_a_run(self, runs_by_experiment, valid_ids):
        """Each valid experiment must have its own run in the signal-analysis experiment."""
        missing = set(valid_ids) - set(runs_by_experiment)
        assert not missing, f"missing MLflow runs for: {missing}"

    def test_required_params_logged(self, runs_by_experiment, valid_ids, reference):
        """Each run must log the experiment id, shape, detrend, and bootstrap config params."""
        for exp in valid_ids:
            params = runs_by_experiment[exp].data.params
            assert params.get("experiment_id") == exp
            assert params.get("detrend") == "linear"
            assert params.get("mc_seed") == "42"
            assert params.get("mc_iterations") == "10000"
            assert float(params["confidence_level"]) == pytest.approx(0.95)
            assert int(params["n_samples"]) == reference[exp]["n_samples"]
            assert float(params["sample_rate_hz"]) == pytest.approx(reference[exp]["sample_rate_hz"])

    def test_required_tags_logged(self, runs_by_experiment, valid_ids):
        """Each run must tag experiment_id and tool=duckdb-signal-analysis."""
        for exp in valid_ids:
            tags = runs_by_experiment[exp].data.tags
            assert tags.get("experiment_id") == exp
            assert tags.get("tool") == "duckdb-signal-analysis"

    def test_stat_metrics_match_recomputation(self, runs_by_experiment, valid_ids, reference):
        """std/rms/skew/kurtosis/min/max metrics must match an independent recomputation."""
        for exp in valid_ids:
            metrics = runs_by_experiment[exp].data.metrics
            ref = reference[exp]["stats"]
            assert metrics["std"] == pytest.approx(ref["std"], rel=1e-3, abs=1e-6)
            assert metrics["rms"] == pytest.approx(ref["rms"], rel=1e-3, abs=1e-6)
            assert metrics["min"] == pytest.approx(ref["min"], rel=1e-3, abs=1e-6)
            assert metrics["max"] == pytest.approx(ref["max"], rel=1e-3, abs=1e-6)
            assert metrics["skew"] == pytest.approx(ref["skew"], abs=1e-2)
            assert metrics["kurtosis"] == pytest.approx(ref["kurtosis"], abs=1e-2)

    def test_dominant_frequency_metrics(self, runs_by_experiment, valid_ids, reference):
        """The three dominant-frequency metrics must match the recomputation within a bin."""
        for exp in valid_ids:
            metrics = runs_by_experiment[exp].data.metrics
            sample_rate, n_samples, _status = _reference.experiment_metadata(exp)
            bin_hz = sample_rate / n_samples
            ref_freqs = [c["frequency_hz"] for c in reference[exp]["dominant_frequencies"]]
            for rank, ref_f in enumerate(ref_freqs, start=1):
                key = f"dominant_freq_{rank}_hz"
                assert key in metrics, f"{exp} missing metric {key}"
                assert abs(metrics[key] - ref_f) <= bin_hz, (
                    f"{exp} {key}={metrics[key]} differs from expected {ref_f}"
                )

    def test_confidence_interval_metrics(self, runs_by_experiment, valid_ids, reference):
        """The CI metrics must bracket the RMS and match the reference width and bounds."""
        for exp in valid_ids:
            metrics = runs_by_experiment[exp].data.metrics
            ref = reference[exp]
            low = metrics["ci_rms_low"]
            high = metrics["ci_rms_high"]
            width = metrics["ci_rms_width"]
            assert low < high, f"{exp} ci_rms_low must be < ci_rms_high"
            assert width == pytest.approx(high - low, abs=1e-6), f"{exp} ci_rms_width inconsistent"
            assert low <= ref["stats"]["rms"] <= high, f"{exp} CI must bracket the RMS"
            ref_width = ref["confidence_interval"]["high"] - ref["confidence_interval"]["low"]
            assert width == pytest.approx(ref_width, rel=0.4), f"{exp} CI width off"
            assert abs(low - ref["confidence_interval"]["low"]) <= 0.2 * ref_width
            assert abs(high - ref["confidence_interval"]["high"]) <= 0.2 * ref_width

    def test_artifacts_logged(self, runs_by_experiment, valid_ids):
        """Each run must attach measurements.csv and analysis.json as artifacts."""
        client = MlflowClient()

        def walk(run_id, path=""):
            for art in client.list_artifacts(run_id, path):
                if art.is_dir:
                    yield from walk(run_id, art.path)
                else:
                    yield art.path

        for exp in valid_ids:
            run_id = runs_by_experiment[exp].info.run_id
            basenames = {p.rsplit("/", 1)[-1] for p in walk(run_id)}
            assert "measurements.csv" in basenames, f"{exp} missing measurements.csv artifact"
            assert "analysis.json" in basenames, f"{exp} missing analysis.json artifact"
