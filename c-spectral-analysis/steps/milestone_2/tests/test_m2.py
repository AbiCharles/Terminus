"""Tests for milestone 2 (DFT and dominant frequencies). Run alone with: pytest tests/test_m2.py

The candidate's /app/signal.c is compiled with an independent C harness under
UndefinedBehaviorSanitizer; each test runs one harness scenario and asserts it
reports "OK" with a zero exit. The spectrum is checked against analytic invariants
(Parseval's relation, the DC term, the known spectral content of synthetic
sinusoids) and an independent reference DFT — on top of the milestone 1 guarantees,
re-checked here so an earlier regression is caught.
"""

import os
import subprocess

import pytest

LIBRARY = "/app/signal.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m2"
CC = os.environ.get("CC", "gcc")
CFLAGS = [
    "-std=c11",
    "-O1",
    "-g",
    "-fno-omit-frame-pointer",
    "-fsanitize=undefined",
    "-fno-sanitize-recover=all",
    "-Wall",
    "-I/app",
]
RUN_ENV = dict(os.environ, UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")


@pytest.fixture(scope="module")
def harness_bin():
    """Compile the candidate library with the sanitized harness once per module."""
    assert os.path.exists(LIBRARY), f"{LIBRARY} not found — implement the library there"
    proc = subprocess.run(
        [CC, *CFLAGS, "-o", BINARY, LIBRARY, HARNESS, "-lm"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"signal.c failed to compile:\n{proc.stderr}"
    return BINARY


def run_scenario(binary, name):
    return subprocess.run([binary, name], capture_output=True, text=True, env=RUN_ENV, timeout=120)


class TestMilestone2:
    """Milestone 2: discrete Fourier transform and dominant-frequency detection."""

    def test_milestone_1_still_holds(self, harness_bin):
        """The milestone 1 statistics must still pass (no regression)."""
        p = run_scenario(harness_bin, "stats_known")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_dc_term_and_parseval(self, harness_bin):
        """X[0] equals the sample sum and Parseval's relation holds across the spectrum."""
        p = run_scenario(harness_bin, "dft_dc_parseval")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_dft_matches_reference(self, harness_bin):
        """Per-bin DFT values match an independent reference DFT."""
        p = run_scenario(harness_bin, "dft_reference")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_dominant_frequencies(self, harness_bin):
        """Dominant bins of a synthetic multi-tone signal match the known components."""
        p = run_scenario(harness_bin, "dominant_bins")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
