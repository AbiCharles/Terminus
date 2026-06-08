"""Tests for milestone 1 (load, stack ops, add/sub, errors). Run alone with: pytest tests/test_m1.py

The candidate's /app/vm.c is compiled together with an independent C harness
(harness.c) under UndefinedBehaviorSanitizer. Each test assembles a bytecode
program, runs it through vm_run(), and asserts the harness reports "OK" (the
returned status code and the exact printed output match the documented
semantics). A UB abort (e.g. an out-of-bounds program read) yields a non-zero
exit and fails the test.
"""

import os
import subprocess

import pytest

LIBRARY = "/app/vm.c"
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


class TestMilestone1:
    """Milestone 1: program loading/decoding, the stack ops, ADD/SUB, and errors."""

    def test_push_and_print(self, harness_bin):
        """PUSH constants and PRINT them in order."""
        p = run_scenario(harness_bin, "push_print")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_pop_discards_top(self, harness_bin):
        """POP removes the top of the stack."""
        p = run_scenario(harness_bin, "pop")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_add_and_sub(self, harness_bin):
        """ADD and SUB pop b then a and push a OP b."""
        p = run_scenario(harness_bin, "add_sub")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_dup_and_swap(self, harness_bin):
        """DUP copies the top; SWAP exchanges the top two."""
        p = run_scenario(harness_bin, "dup_swap")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_stack_underflow(self, harness_bin):
        """An op needing more operands than are present returns VM_ERR_STACK_UNDERFLOW."""
        p = run_scenario(harness_bin, "underflow")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_stack_overflow(self, harness_bin):
        """Pushing beyond VM_STACK_CAPACITY returns VM_ERR_STACK_OVERFLOW."""
        p = run_scenario(harness_bin, "overflow")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_bad_opcode(self, harness_bin):
        """An undefined opcode byte returns VM_ERR_OPCODE."""
        p = run_scenario(harness_bin, "bad_opcode")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_truncated_operand(self, harness_bin):
        """An operand running past the program end returns VM_ERR_OPERAND (no OOB read)."""
        p = run_scenario(harness_bin, "truncated")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_missing_halt(self, harness_bin):
        """Reaching the program end with no HALT returns VM_ERR_NO_HALT."""
        p = run_scenario(harness_bin, "no_halt")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
