"""Tests for milestone 2 (arithmetic, comparisons, locals). Run alone with: pytest tests/test_m2.py

The candidate's /app/vm.c is compiled with an independent C harness under
UndefinedBehaviorSanitizer; each test assembles a bytecode program and asserts
the harness reports "OK". Arithmetic must wrap in two's complement (a naive
signed add/mul that overflows aborts under UBSan), division must reject a zero
divisor, and locals must be bounds-checked — on top of the milestone 1 behaviour,
re-checked here.
"""

import os
import subprocess

import pytest

LIBRARY = "/app/vm.c"
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
RUN_ENV = dict(os.environ, UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")


@pytest.fixture(scope="module")
def harness_bin():
    """Compile the candidate VM with the sanitized harness once per module."""
    assert os.path.exists(LIBRARY), f"{LIBRARY} not found — implement the VM there"
    proc = subprocess.run(
        [CC, *CFLAGS, "-o", BINARY, LIBRARY, HARNESS],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"vm.c failed to compile:\n{proc.stderr}"
    return BINARY


def run_scenario(binary, name):
    return subprocess.run([binary, name], capture_output=True, text=True, env=RUN_ENV, timeout=120)


class TestMilestone2:
    """Milestone 2: full arithmetic, comparisons, and local variables."""

    def test_milestone_1_still_holds(self, harness_bin):
        """The milestone 1 ADD/SUB behaviour must still pass (no regression)."""
        p = run_scenario(harness_bin, "add_sub")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_mul_div_mod(self, harness_bin):
        """MUL, DIV and MOD produce the documented results."""
        p = run_scenario(harness_bin, "muldivmod")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_division_truncates_toward_zero(self, harness_bin):
        """DIV/MOD with a negative operand truncate toward zero (C semantics)."""
        p = run_scenario(harness_bin, "div_trunc")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_division_by_zero(self, harness_bin):
        """A zero divisor returns VM_ERR_DIV_ZERO."""
        p = run_scenario(harness_bin, "div_zero")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_wrapping_arithmetic(self, harness_bin):
        """Overflowing ADD/MUL wrap in two's complement (naive signed math aborts under UBSan)."""
        p = run_scenario(harness_bin, "wrapping")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_division_overflow_wraps(self, harness_bin):
        """INT64_MIN / -1 wraps to INT64_MIN and INT64_MIN % -1 is 0 (no UB)."""
        p = run_scenario(harness_bin, "div_overflow")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_negate(self, harness_bin):
        """NEG negates the top, wrapping for INT64_MIN."""
        p = run_scenario(harness_bin, "neg")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_comparisons(self, harness_bin):
        """LT/EQ/GT push 1 or 0."""
        p = run_scenario(harness_bin, "compare")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_locals_load_store(self, harness_bin):
        """LOAD/STORE move values to and from local slots; untouched slots read 0."""
        p = run_scenario(harness_bin, "locals")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_local_slot_out_of_range(self, harness_bin):
        """A local slot index >= VM_LOCALS_COUNT returns VM_ERR_OPERAND."""
        p = run_scenario(harness_bin, "bad_slot")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
