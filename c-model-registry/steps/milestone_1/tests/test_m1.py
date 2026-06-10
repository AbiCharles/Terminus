"""Tests for milestone 1. Run alone with: pytest tests/test_m1.py

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
BINARY = "/tmp/harness_m1"
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


class TestMilestone1:
    def test_basic(self, harness_bin):
        """Register versions, count them, and read back metrics exactly."""
        p = run_scenario(harness_bin, "basic", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_tags(self, harness_bin):
        """Set, overwrite and read string tags; absent tag/version/model report errors."""
        p = run_scenario(harness_bin, "tags", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_reset(self, harness_bin):
        """reg_reset empties a populated registry and leaves it reusable."""
        p = run_scenario(harness_bin, "reset", 60)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_scale(self, harness_bin):
        """Thousands of models, versions and tags are stored and retrieved correctly, UB-free."""
        p = run_scenario(harness_bin, "scale", 120)
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

