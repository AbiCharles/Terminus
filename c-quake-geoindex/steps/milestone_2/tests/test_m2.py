"""Tests for milestone 2 (removal under churn). Run alone with: pytest tests/test_m2.py

The candidate's /app/geoindex.c is compiled with an independent harness under
UndefinedBehaviorSanitizer. These scenarios remove events and run heavy
insert/remove churn, asserting the index keeps the right size and returns the
right radius-query results throughout, with no undefined behavior. The harness
mirrors every event so it checks against a brute-force scan, never the index's
own bookkeeping.
"""

import os
import subprocess

import pytest

GEOINDEX = "/app/geoindex.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m2"
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


class TestMilestone2:
    """Milestone 2: gi_remove with correct bucket maintenance under churn."""

    def test_remove_reflects_in_size_and_queries(self, harness_bin):
        """After removals the size and radius-query results match the brute-force mirror."""
        p = run_scenario(harness_bin, "remove_basic", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_remove_absent_and_double_remove(self, harness_bin):
        """Removing an absent id (or an already-removed id) returns nonzero, not a crash."""
        p = run_scenario(harness_bin, "remove_nonexistent", 30)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_remove_everything(self, harness_bin):
        """Removing all events leaves size 0 and empty queries, sanitizer-clean."""
        p = run_scenario(harness_bin, "remove_all", 30)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_heavy_churn_is_correct_and_clean(self, harness_bin):
        """Thirty rounds of insert/remove with id reuse stay correct and UB-free."""
        p = run_scenario(harness_bin, "churn", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_large_scale_churn_stays_efficient(self, harness_bin):
        """200k inserts, 80k removes, 60k more inserts, then 20k queries — the index
        must stay efficient and exact under churn (a flat scan times out)."""
        p = run_scenario(harness_bin, "scale_churn", 120)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
