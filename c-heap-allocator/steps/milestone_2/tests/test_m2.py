"""Tests for milestone 2 (reuse, splitting, calloc). Run alone with: pytest tests/test_m2.py

The candidate's /app/allocator.c is compiled with an independent C harness under
UndefinedBehaviorSanitizer; each test runs one harness
scenario and asserts it reports "OK" with a zero exit. These scenarios require
that freed blocks are genuinely reclaimed and that large free regions are split,
on top of the milestone 1 guarantees (which are re-checked here so a regression
in earlier behavior is caught).
"""

import os
import subprocess

import pytest

ALLOCATOR = "/app/allocator.c"
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
    return subprocess.run([binary, name], capture_output=True, text=True, env=RUN_ENV, timeout=180)


class TestMilestone2:
    """Milestone 2: freed blocks are reused, large blocks split, calloc zeroes safely."""

    def test_milestone_1_still_holds(self, harness_bin):
        """The milestone 1 alignment/overlap guarantees must still pass (no regression)."""
        p = run_scenario(harness_bin, "align")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_freed_memory_is_reused(self, harness_bin):
        """A long allocate/free churn within the arena succeeds only if freed blocks are reused."""
        p = run_scenario(harness_bin, "reuse")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_free_block_is_split(self, harness_bin):
        """Two smaller allocations can be carved from one larger freed region."""
        p = run_scenario(harness_bin, "split")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_calloc_zeroes(self, harness_bin):
        """xcalloc returns fully zeroed, writable memory."""
        p = run_scenario(harness_bin, "calloc_zero")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_calloc_overflow_rejected(self, harness_bin):
        """xcalloc detects nmemb*size multiplication overflow and returns NULL."""
        p = run_scenario(harness_bin, "calloc_overflow")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_churn_preserves_all_live_blocks(self, harness_bin):
        """A long randomized allocate/free workload never corrupts a live block."""
        p = run_scenario(harness_bin, "churn")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
