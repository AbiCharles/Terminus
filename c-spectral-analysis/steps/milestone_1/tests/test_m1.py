"""Tests for milestone 1 (time-domain statistics). Run alone with: pytest tests/test_m1.py

The candidate's /app/signal.c is compiled together with an independent C harness
(harness.c) under UndefinedBehaviorSanitizer. Each test runs one harness scenario
in its own process and asserts it reports "OK" with a zero exit status. The harness
recomputes every statistic by direct summation, so a wrong formula (for example a
sample instead of a population variance) is rejected, and a UB abort yields a
non-zero exit.
"""

import os
import subprocess

import pytest

LIBRARY = "/app/signal.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m1"
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


class TestMilestone1:
    """Milestone 1: time-domain statistics (mean, variance, stddev, rms, min, max)."""

    def test_known_values(self, harness_bin):
        """Statistics on a hand-checked array match exactly (population variance)."""
        p = run_scenario(harness_bin, "stats_known")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_random_matches_recomputation(self, harness_bin):
        """Statistics on a large signal match an independent direct recomputation."""
        p = run_scenario(harness_bin, "stats_random")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_edge_cases(self, harness_bin):
        """n == 0 returns SIG_ERR and a single sample yields zero variance."""
        p = run_scenario(harness_bin, "stats_edge")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
