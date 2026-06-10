"""Tests for milestone 3. Run alone with: pytest tests/test_m3.py

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
BINARY = "/tmp/harness_m3"
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


class TestMilestone3:
    def test_roundtrip(self, harness_bin):
        """A populated registry survives save/reset/load exactly (versions, metrics, tags, aliases)."""
        p = run_scenario(harness_bin, "roundtrip", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_adversarial_strings(self, harness_bin):
        """Tag values with newlines/colons/delimiters/empty/long survive the round-trip."""
        p = run_scenario(harness_bin, "adversarial_strings", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_state_roundtrip(self, harness_bin):
        """Aliases and rollback history survive save/load; rollback still works after loading."""
        p = run_scenario(harness_bin, "state_roundtrip", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_load_replaces(self, harness_bin):
        """Loading replaces the in-memory registry entirely."""
        p = run_scenario(harness_bin, "load_replaces", 90)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_large_state_roundtrip(self, harness_bin):
        """A large promoted/aliased/newline-tagged registry round-trips exactly."""
        p = run_scenario(harness_bin, "full_state", 120)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_empty_registry_roundtrip(self, harness_bin):
        """Saving and loading an empty registry yields an empty, reusable registry."""
        p = run_scenario(harness_bin, "empty_save_load", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
