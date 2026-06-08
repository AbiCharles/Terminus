Now extend `vm_run` in `/app/vm.c` with the rest of the arithmetic, the comparisons, and local variables.

- `MUL`, `DIV`, `MOD`, `NEG`: implement the full integer arithmetic. All arithmetic is on signed 64-bit integers with **two's-complement wrapping** — an overflowing `ADD`, `SUB`, `MUL`, or `NEG` must wrap rather than trap, so compute through unsigned arithmetic to avoid signed-overflow undefined behavior (UBSan will catch a naive signed overflow). `DIV` and `MOD` truncate toward zero (C semantics); a zero divisor returns `VM_ERR_DIV_ZERO`. Remember that the single pair `INT64_MIN / -1` overflows and must wrap.
- `LT`, `EQ`, `GT`: pop `b` then `a` and push `1` if the comparison holds, otherwise `0`.
- `LOAD` and `STORE`: the VM has `VM_LOCALS_COUNT` local slots, all initialized to zero. `LOAD <slot>` pushes `locals[slot]`; `STORE <slot>` pops the top into `locals[slot]`. A slot index that is `>= VM_LOCALS_COUNT` is invalid and returns `VM_ERR_OPERAND`.

Everything from milestone 1 (loading, the stack ops, `ADD`/`SUB`, `PRINT`/`HALT`, and all the milestone 1 error cases) must continue to work.
