"""Tests for milestone 3 (control flow, loops, limits). Run alone with: pytest tests/test_m3.py

The candidate's /app/vm.c is compiled with an independent C harness under
UndefinedBehaviorSanitizer; each test assembles a bytecode program and asserts
the harness reports "OK". Jumps must validate their target, conditional branches
must consume the condition, real loops must run to a correct result, and an
out-of-range jump or a non-terminating program must be reported rather than
crash or hang — on top of the milestone 1 and 2 behaviour, re-checked here.
"""

import os
import subprocess

import pytest

LIBRARY = "/app/vm.c"
HARNESS = os.path.join(os.path.dirname(__file__), "harness.c")
BINARY = "/tmp/harness_m3"
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


class TestMilestone3:
    """Milestone 3: jumps, conditional branches, loops, and execution limits."""

    def test_milestone_2_still_holds(self, harness_bin):
        """The milestone 2 arithmetic must still pass (no regression)."""
        p = run_scenario(harness_bin, "muldivmod")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_unconditional_jump(self, harness_bin):
        """JMP transfers control, skipping the intervening instructions."""
        p = run_scenario(harness_bin, "jmp")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_conditional_branches(self, harness_bin):
        """JZ/JNZ pop the condition and branch (taken and not-taken)."""
        p = run_scenario(harness_bin, "conditional")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_counting_loop(self, harness_bin):
        """A loop using locals and a conditional branch computes the right result."""
        p = run_scenario(harness_bin, "loop")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_out_of_range_jump(self, harness_bin):
        """A jump target outside [0, len) returns VM_ERR_BAD_JUMP."""
        p = run_scenario(harness_bin, "bad_jump")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"

    def test_step_limit(self, harness_bin):
        """A non-terminating program is stopped with VM_ERR_STEP_LIMIT rather than hanging."""
        p = run_scenario(harness_bin, "infinite_loop")
        assert p.returncode == 0 and "OK" in p.stdout, f"stdout={p.stdout}\nstderr={p.stderr}"
