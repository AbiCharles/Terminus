"""Tests for milestone 2. Run alone with: pytest tests/test_m2.py

The candidate's /app/registry.c is compiled with an independent harness under
UndefinedBehaviorSanitizer. Each test runs one harness scenario in its own
process and asserts it prints "OK" with exit 0; a wrong answer or a sanitizer
abort fails the test. The harness verifies the registry against an independent
reference, never its own bookkeeping.
"""

import os
import subprocess

import pytest

REGISTRY = "/app/registry.c"
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
    assert os.path.exists(REGISTRY), f"{REGISTRY} not found — implement the registry there"
    proc = subprocess.run([CC, *CFLAGS, "-o", BINARY, REGISTRY, HARNESS],
                          capture_output=True, text=True)
    assert proc.returncode == 0, f"registry.c failed to compile:\n{proc.stderr}"
    return BINARY


def run_scenario(binary, name, timeout):
    return subprocess.run([binary, name], capture_output=True, text=True, env=RUN_ENV, timeout=timeout)


class TestMilestone2:
    def test_gates(self, harness_bin):
        """reg_evaluate_gate matches the policy formula and records validation_status tags."""
        p = run_scenario(harness_bin, "gates", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_aliases(self, harness_bin):
        """Aliases set, move and read back independently; absent cases report correctly."""
        p = run_scenario(harness_bin, "aliases", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_promote(self, harness_bin):
        """Promotion selects the highest-AUC gate-passing version; no pass promotes nothing."""
        p = run_scenario(harness_bin, "promote", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_rollback_deep(self, harness_bin):
        """Many promote/rollback cycles follow the champion-history stack exactly."""
        p = run_scenario(harness_bin, "rollback_deep", 120)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

