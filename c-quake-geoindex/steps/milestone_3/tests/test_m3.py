"""Tests for milestone 3 (Gardner-Knopoff declustering). Run alone with: pytest tests/test_m3.py

The candidate's /app/geoindex.c is compiled with an independent harness under
UndefinedBehaviorSanitizer. Each scenario builds the index and checks
gi_decluster against an independent brute-force Gardner-Knopoff implementation
kept inside the harness, so only the exact surviving-mainshock set (ascending
ids) passes. Declustering must not mutate the index.
"""

import os
import subprocess

import pytest

GEOINDEX = "/app/geoindex.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m3"
CC = os.environ.get("CC", "gcc")
CFLAGS = [
    "-std=c11", "-O2", "-g", "-fno-omit-frame-pointer",
    "-fsanitize=undefined", "-fno-sanitize-recover=all", "-Wall", "-I/app",
]
RUN_ENV = dict(os.environ, UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")


@pytest.fixture(scope="module")
def harness_bin():
    assert os.path.exists(GEOINDEX), f"{GEOINDEX} not found — implement the index there"
    proc = subprocess.run([CC, *CFLAGS, "-o", BINARY, GEOINDEX, HARNESS, "-lm"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, f"geoindex.c failed to compile:\n{proc.stderr}"
    return BINARY


def run_scenario(binary, name, timeout):
    return subprocess.run([binary, name], capture_output=True, text=True, env=RUN_ENV, timeout=timeout)


class TestMilestone3:
    """Milestone 3: gi_decluster (Gardner-Knopoff) over the indexed catalog."""

    def test_random_catalog_matches_reference(self, harness_bin):
        """Declustering a random catalog matches the brute-force Gardner-Knopoff set."""
        p = run_scenario(harness_bin, "random", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_clustered_keeps_mainshocks(self, harness_bin):
        """Injected aftershock clusters are removed and every mainshock survives."""
        p = run_scenario(harness_bin, "clustered", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_decluster_after_removals(self, harness_bin):
        """Declustering a catalog that has had events removed matches the reference."""
        p = run_scenario(harness_bin, "after_remove", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_decluster_does_not_mutate_index(self, harness_bin):
        """gi_decluster leaves the index unchanged (size preserved, repeatable)."""
        p = run_scenario(harness_bin, "unchanged", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_survivor_buffer_capacity(self, harness_bin):
        """When survivors exceed the buffer, return the true total and the smallest ids."""
        p = run_scenario(harness_bin, "capacity", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
