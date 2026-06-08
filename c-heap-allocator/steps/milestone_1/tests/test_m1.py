"""Tests for milestone 1 (arena allocation). Run alone with: pytest tests/test_m1.py

The candidate's /app/allocator.c is compiled together with an independent C
harness (harness.c) under UndefinedBehaviorSanitizer. Each
test runs one harness scenario in its own process and asserts it reports "OK"
with a zero exit status; a sanitizer abort or a violated invariant (overlap,
misalignment, corruption, or never reporting exhaustion) yields a non-zero exit
and fails the test. The harness keeps its own record of every live allocation,
so it verifies correctness without trusting the allocator's bookkeeping.
"""

import os
import subprocess

import pytest

ALLOCATOR = "/app/allocator.c"
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
RUN_ENV = dict(
    os.environ,
    UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1",
)


@pytest.fixture(scope="module")
def harness_bin():
    """Compile the candidate allocator with the sanitized harness once per module."""
    assert os.path.exists(ALLOCATOR), f"{ALLOCATOR} not found — implement the allocator there"
    proc = subprocess.run(
        [CC, *CFLAGS, "-o", BINARY, ALLOCATOR, HARNESS],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"allocator.c failed to compile:\n{proc.stderr}"
    return BINARY


def run_scenario(binary, name):
    return subprocess.run([binary, name], capture_output=True, text=True, env=RUN_ENV, timeout=120)


class TestMilestone1:
    """Milestone 1: a working fixed-arena allocator (alignment, bounds, integrity)."""

    def test_alignment_and_no_overlap(self, harness_bin):
        """Every returned pointer is 16-byte aligned and never overlaps a live block."""
        p = run_scenario(harness_bin, "align")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_data_integrity_across_frees(self, harness_bin):
        """Live blocks keep their contents while other blocks are freed and new ones allocated."""
        p = run_scenario(harness_bin, "integrity")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_capacity_exhaustion(self, harness_bin):
        """The arena reports exhaustion with NULL under pressure instead of overrunning."""
        p = run_scenario(harness_bin, "oom")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_zero_and_null_edge_cases(self, harness_bin):
        """xmalloc(0) returns NULL and xfree(NULL) is a safe no-op."""
        p = run_scenario(harness_bin, "zero_null")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
