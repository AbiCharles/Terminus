"""Tests for milestone 2 (Compute Signal Statistics). Run alone with: pytest tests/test_m2.py

These tests open each valid experiment's /app/artifacts/<id>/analysis.json and check
it against an INDEPENDENT recomputation from the database (see _reference.py): the
detrended basic statistics, the three FFT-dominant frequencies, and the seeded
bootstrap RMS confidence interval. Deterministic quantities are matched tightly;
the bootstrap interval is matched loosely enough to absorb benign RNG-stream
differences while still rejecting a missing or mis-scaled interval.
"""

import json
import subprocess
from pathlib import Path

import pytest

import _reference

ARTIFACTS = Path("/app/artifacts")


@pytest.fixture(scope="module")
def valid_ids():
    ids = _reference.valid_experiment_ids()
    assert ids, "no valid experiments found in the database"
    return ids


@pytest.fixture(scope="module")
def analyses(valid_ids):
    out = {}
    for exp in valid_ids:
        path = ARTIFACTS / exp / "analysis.json"
        assert path.exists(), f"{exp} missing analysis.json — milestone 2 not completed"
        out[exp] = json.loads(path.read_text())
    return out


@pytest.fixture(scope="module")
def reference(valid_ids):
    return {exp: _reference.compute_analysis(exp) for exp in valid_ids}


class TestMilestone2:
    """Milestone 2: detrended statistics, dominant frequencies, and bootstrap CI."""

    def test_top_level_fields(self, analyses, reference):
        """Each analysis.json must report the experiment id, shape, and linear detrend."""
        for exp, got in analyses.items():
            ref = reference[exp]
            assert got["experiment_id"] == exp
            assert int(got["n_samples"]) == ref["n_samples"]
            assert float(got["sample_rate_hz"]) == pytest.approx(ref["sample_rate_hz"])
            assert got["detrend"] == "linear"

    def test_basic_stats_match_recomputation(self, analyses, reference):
        """mean/std/min/max/rms/skew/kurtosis must match an independent recomputation."""
        for exp, got in analyses.items():
            stats = got["stats"]
            ref = reference[exp]["stats"]
            assert stats["mean"] == pytest.approx(ref["mean"], abs=1e-3)
            assert stats["std"] == pytest.approx(ref["std"], rel=1e-3, abs=1e-6)
            assert stats["rms"] == pytest.approx(ref["rms"], rel=1e-3, abs=1e-6)
            assert stats["min"] == pytest.approx(ref["min"], rel=1e-3, abs=1e-6)
            assert stats["max"] == pytest.approx(ref["max"], rel=1e-3, abs=1e-6)
            assert stats["skew"] == pytest.approx(ref["skew"], abs=1e-2)
            assert stats["kurtosis"] == pytest.approx(ref["kurtosis"], abs=1e-2)

    def test_dominant_frequencies(self, analyses, reference):
        """The three dominant frequencies must match (within a bin) and be ordered by magnitude."""
        for exp, got in analyses.items():
            components = got["dominant_frequencies"]
            assert len(components) == 3, f"{exp} must report exactly three dominant frequencies"
            magnitudes = [float(c["magnitude"]) for c in components]
            assert magnitudes == sorted(magnitudes, reverse=True), (
                f"{exp} dominant frequencies must be ordered strongest first"
            )
            assert all(m > 0 for m in magnitudes), f"{exp} magnitudes must be positive"

            sample_rate, n_samples, _status = _reference.experiment_metadata(exp)
            bin_hz = sample_rate / n_samples
            got_freqs = sorted(float(c["frequency_hz"]) for c in components)
            ref_freqs = sorted(
                float(c["frequency_hz"]) for c in reference[exp]["dominant_frequencies"]
            )
            for got_f, ref_f in zip(got_freqs, ref_freqs):
                assert abs(got_f - ref_f) <= bin_hz, (
                    f"{exp} dominant frequency {got_f} differs from expected {ref_f}"
                )

    def test_confidence_interval(self, analyses, reference):
        """The 95% bootstrap RMS interval must bracket the RMS and match the reference width."""
        for exp, got in analyses.items():
            interval = got["confidence_interval"]
            ref = reference[exp]
            assert interval["statistic"] == "rms"
            assert float(interval["level"]) == pytest.approx(0.95)
            assert int(interval["n_iterations"]) == 10000
            assert int(interval["seed"]) == 42

            low = float(interval["low"])
            high = float(interval["high"])
            assert low < high, f"{exp} CI must have low < high"
            assert low <= ref["stats"]["rms"] <= high, f"{exp} CI must bracket the RMS"

            ref_low = ref["confidence_interval"]["low"]
            ref_high = ref["confidence_interval"]["high"]
            ref_width = ref_high - ref_low
            assert (high - low) == pytest.approx(ref_width, rel=0.4), (
                f"{exp} CI width {high - low:.5f} differs from reference {ref_width:.5f}"
            )
            assert abs(low - ref_low) <= 0.2 * ref_width, f"{exp} CI lower bound is off"
            assert abs(high - ref_high) <= 0.2 * ref_width, f"{exp} CI upper bound is off"

    def test_experiment_id_flag_scopes_output(self, valid_ids, tmp_path):
        """analyze --experiment-id must scope analysis.json output to the requested experiment."""
        target = valid_ids[0]
        subprocess.run(
            ["python", "/app/signal_analysis.py", "analyze",
             "--experiment-id", target, "--output-dir", str(tmp_path)],
            check=True,
        )
        assert (tmp_path / target / "analysis.json").exists(), f"scoped analyze did not produce {target}"
        for other in valid_ids[1:]:
            assert not (tmp_path / other).exists(), (
                f"{other} produced even though only {target} was requested"
            )

    def test_experiment_id_invalid_skipped(self, tmp_path):
        """A non-valid or unknown --experiment-id must be skipped, producing no output."""
        subprocess.run(
            ["python", "/app/signal_analysis.py", "analyze",
             "--experiment-id", "NOSUCH", "--output-dir", str(tmp_path)],
            check=True,
        )
        assert not any(tmp_path.iterdir()), "unknown experiment id must produce no analyze output"
