"""Tests for milestone 3 (coalescing, realloc, stats). Run alone with: pytest tests/test_m3.py

The candidate's /app/allocator.c is compiled with an independent C harness under
AddressSanitizer + UndefinedBehaviorSanitizer; each test runs one harness
scenario and asserts it reports "OK" with a zero exit. These scenarios require
adjacent free blocks to coalesce, xrealloc to preserve data while growing,
shrinking and relocating, and heap_stats to report exact live accounting — on
top of the milestone 1 and 2 guarantees (re-checked here).
"""

import os
import subprocess

import pytest

ALLOCATOR = "/app/allocator.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m3"
CC = os.environ.get("CC", "gcc")
CFLAGS = [
    "-std=c11",
    "-O1",
    "-g",
    "-fno-omit-frame-pointer",
    "-fsanitize=address,undefined",
    "-fno-sanitize-recover=all",
    "-Wall",
    "-I/app",
]
RUN_ENV = dict(
    os.environ,
    ASAN_OPTIONS="abort_on_error=1:detect_leaks=0",
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


class TestMilestone3:
    """Milestone 3: coalescing, realloc semantics, and exact heap statistics."""

    def test_milestone_2_still_holds(self, harness_bin):
        """The milestone 2 reuse guarantee must still pass (no regression)."""
        p = run_scenario(harness_bin, "reuse")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_adjacent_free_blocks_coalesce(self, harness_bin):
        """After freeing many small blocks, a large allocation succeeds only via coalescing."""
        p = run_scenario(harness_bin, "coalesce")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_realloc_grow_preserves_data(self, harness_bin):
        """Growing a block via xrealloc preserves its original contents."""
        p = run_scenario(harness_bin, "realloc_grow")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_realloc_shrink_preserves_data(self, harness_bin):
        """Shrinking a block via xrealloc preserves its leading contents."""
        p = run_scenario(harness_bin, "realloc_shrink")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_realloc_null_and_zero_semantics(self, harness_bin):
        """xrealloc(NULL, n) acts as xmalloc and xrealloc(p, 0) frees and returns NULL."""
        p = run_scenario(harness_bin, "realloc_null_zero")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_realloc_failure_preserves_original(self, harness_bin):
        """A failed (unsatisfiable) xrealloc returns NULL and leaves the original block intact."""
        p = run_scenario(harness_bin, "realloc_fail")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_heap_stats_exact(self, harness_bin):
        """heap_stats reports exact bytes_in_use and live_allocations for a known trace."""
        p = run_scenario(harness_bin, "stats")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_fragmentation_reclaimed(self, harness_bin):
        """After freeing a varied workload, coalescing recovers ~all space as one block."""
        p = run_scenario(harness_bin, "frag")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
