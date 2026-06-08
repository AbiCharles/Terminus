Finally, complete `vm_run` in `/app/vm.c` with control flow.

- `JMP <addr>`: set the program counter to the 32-bit little-endian target address.
- `JZ <addr>` and `JNZ <addr>`: pop the top value as the condition; `JZ` branches when it is zero, `JNZ` when it is non-zero. When the branch is not taken, execution falls through to the instruction after the jump.
- Validate every taken jump: a target that is not within `[0, len)` returns `VM_ERR_BAD_JUMP`. (A target need not land on an instruction boundary; if it lands mid-instruction the bytes there are simply decoded as the next instruction.)
- Programs may now loop. Guard against non-termination with the instruction budget: if execution runs more than `VM_MAX_STEPS` instructions, stop and return `VM_ERR_STEP_LIMIT`.

With jumps, locals, and comparisons in place, a real loop — for example summing the integers from 1 to N with a counter and an accumulator in local slots — must run to completion and produce the correct result. All of the milestone 1 and milestone 2 behaviour must continue to work.
