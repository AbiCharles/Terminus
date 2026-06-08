"""Tests for milestone 3 (spectral SNR, confidence interval, gate). Run alone with: pytest tests/test_m3.py

The candidate's /app/signal.c is compiled with an independent C harness under
UndefinedBehaviorSanitizer; each test runs one harness scenario and asserts it
reports "OK" with a zero exit. Spectral SNR is checked against an independent
reference power computation, the confidence interval against the population
statistics, and the gate against the SNR it is derived from — on top of the
milestone 1 and 2 guarantees, re-checked here.
"""

import os
import subprocess

import pytest

LIBRARY = "/app/signal.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m3"
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


class TestMilestone3:
    """Milestone 3: spectral SNR, mean confidence interval, and the acceptance gate."""

    def test_milestone_2_still_holds(self, harness_bin):
        """The milestone 2 reference-DFT guarantee must still pass (no regression)."""
        p = run_scenario(harness_bin, "dft_reference")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_spectral_snr_value(self, harness_bin):
        """Spectral SNR (dB) matches an independent reference power computation."""
        p = run_scenario(harness_bin, "snr_value")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_spectral_snr_ordering(self, harness_bin):
        """A strong tone has markedly higher spectral SNR than a noise-only signal."""
        p = run_scenario(harness_bin, "snr_ordering")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_mean_confidence_interval(self, harness_bin):
        """The 95% mean confidence interval matches the population statistics; n==0 errors."""
        p = run_scenario(harness_bin, "ci")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_acceptance_gate(self, harness_bin):
        """The gate accepts a strong tone and rejects noise, consistent with the SNR."""
        p = run_scenario(harness_bin, "gate")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
