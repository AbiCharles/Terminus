"""Tests for milestone 1 (spatial insert + radius query). Run alone with: pytest tests/test_m1.py

The candidate's /app/geoindex.c is compiled together with an independent C
harness (harness.c) under UndefinedBehaviorSanitizer. Each test runs one harness
scenario in its own process and asserts it reports "OK" with a zero exit status;
a sanitizer abort, a wrong query result, or a timeout (a flat per-query scan
cannot finish the large-N scenario in time) yields a non-zero exit and fails the
test. The harness keeps its own record of every inserted event, so it verifies
the index against a brute-force haversine scan without trusting its bookkeeping.
"""

import os
import subprocess

import pytest

GEOINDEX = "/app/geoindex.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m1"
CC = os.environ.get("CC", "gcc")
CFLAGS = [
    "-std=c11",
    "-O2",
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
    """Compile the candidate index with the sanitized harness once per module."""
    assert os.path.exists(GEOINDEX), f"{GEOINDEX} not found — implement the index there"
    proc = subprocess.run(
        [CC, *CFLAGS, "-o", BINARY, GEOINDEX, HARNESS, "-lm"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"geoindex.c failed to compile:\n{proc.stderr}"
    return BINARY


def run_scenario(binary, name, timeout):
    return subprocess.run([binary, name], capture_output=True, text=True, env=RUN_ENV, timeout=timeout)


class TestMilestone1:
    """Milestone 1: a correct, efficient spatial index (insert + radius query)."""

    def test_basic_queries_match_bruteforce(self, harness_bin):
        """Random radius queries return exactly the brute-force match set, ids ascending."""
        p = run_scenario(harness_bin, "basic", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_antimeridian_and_pole_wraparound(self, harness_bin):
        """Queries near +-180 longitude and the poles must include wrapped/high-lat events."""
        p = run_scenario(harness_bin, "wrap", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_result_buffer_capacity(self, harness_bin):
        """When matches exceed the buffer, return the true total and the smallest ids."""
        p = run_scenario(harness_bin, "capacity", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_empty_index(self, harness_bin):
        """Querying an empty index returns zero and is sanitizer-clean."""
        p = run_scenario(harness_bin, "empty", 30)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_reset_empties_and_reuses(self, harness_bin):
        """gi_reset empties a populated index (size 0, empty queries) and leaves it reusable."""
        p = run_scenario(harness_bin, "reset", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_large_catalog_is_efficient(self, harness_bin):
        """250k events and 30k queries must finish well within the limit — a flat
        per-query scan times out, so the index must bucket events spatially."""
        p = run_scenario(harness_bin, "scale", 120)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
