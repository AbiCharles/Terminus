#!/bin/bash
set -euo pipefail

# Milestone 3 oracle: write the complete reference VM to /app/vm.c. A single
# correct vm_run implementation (covering control flow (JMP/JZ/JNZ), loops, jump-target validation and the step limit, plus the rest) satisfies this
# milestone and the others, so each milestone installs the same vetted source;
# the milestone's own verifier exercises the relevant subset of opcodes.
cat > /app/vm.c <<'VM_EOF'
#include "vm.h"

/*
 * Reference bytecode VM: a direct decode/dispatch loop over an int64 operand
 * stack. All arithmetic is done through uint64_t so signed overflow wraps in
 * two's complement without undefined behavior; division special-cases the one
 * overflowing pair (INT64_MIN / -1). Every operand read and jump target is
 * bounds-checked against the program length before use.
 */

int vm_run(const uint8_t *code, size_t len, int64_t *out, size_t out_cap, size_t *out_len) {
    int64_t stack[VM_STACK_CAPACITY];
    int64_t locals[VM_LOCALS_COUNT] = {0};
    size_t sp = 0;
    size_t produced = 0;
    size_t pc = 0;
    uint64_t steps = 0;

#define FINISH(code_) do { if (out_len) *out_len = produced; return (code_); } while (0)

    for (;;) {
        if (steps++ >= VM_MAX_STEPS) FINISH(VM_ERR_STEP_LIMIT);
        if (pc >= len) FINISH(VM_ERR_NO_HALT);
        uint8_t op = code[pc];
        switch (op) {
            case OP_PUSH: {
                if (pc + 1u + 8u > len) FINISH(VM_ERR_OPERAND);
                uint64_t v = 0;
                for (int i = 0; i < 8; i++) v |= (uint64_t)code[pc + 1 + (size_t)i] << (8 * i);
                if (sp >= VM_STACK_CAPACITY) FINISH(VM_ERR_STACK_OVERFLOW);
                stack[sp++] = (int64_t)v;
                pc += 9;
                break;
            }
            case OP_POP:
                if (sp < 1) FINISH(VM_ERR_STACK_UNDERFLOW);
                sp--;
                pc += 1;
                break;
            case OP_DUP:
                if (sp < 1) FINISH(VM_ERR_STACK_UNDERFLOW);
                if (sp >= VM_STACK_CAPACITY) FINISH(VM_ERR_STACK_OVERFLOW);
                stack[sp] = stack[sp - 1];
                sp++;
                pc += 1;
                break;
            case OP_SWAP: {
                if (sp < 2) FINISH(VM_ERR_STACK_UNDERFLOW);
                int64_t t = stack[sp - 1];
                stack[sp - 1] = stack[sp - 2];
                stack[sp - 2] = t;
                pc += 1;
                break;
            }
            case OP_ADD:
            case OP_SUB:
            case OP_MUL:
            case OP_DIV:
            case OP_MOD:
            case OP_LT:
            case OP_EQ:
            case OP_GT: {
                if (sp < 2) FINISH(VM_ERR_STACK_UNDERFLOW);
                int64_t b = stack[sp - 1];
                int64_t a = stack[sp - 2];
                int64_t r;
                switch (op) {
                    case OP_ADD: r = (int64_t)((uint64_t)a + (uint64_t)b); break;
                    case OP_SUB: r = (int64_t)((uint64_t)a - (uint64_t)b); break;
                    case OP_MUL: r = (int64_t)((uint64_t)a * (uint64_t)b); break;
                    case OP_DIV:
                        if (b == 0) FINISH(VM_ERR_DIV_ZERO);
                        r = (a == INT64_MIN && b == -1) ? INT64_MIN : a / b;
                        break;
                    case OP_MOD:
                        if (b == 0) FINISH(VM_ERR_DIV_ZERO);
                        r = (a == INT64_MIN && b == -1) ? 0 : a % b;
                        break;
                    case OP_LT: r = (a < b) ? 1 : 0; break;
                    case OP_EQ: r = (a == b) ? 1 : 0; break;
                    default:    r = (a > b) ? 1 : 0; break; /* OP_GT */
                }
                sp -= 1;
                stack[sp - 1] = r;
                pc += 1;
                break;
            }
            case OP_NEG:
                if (sp < 1) FINISH(VM_ERR_STACK_UNDERFLOW);
                stack[sp - 1] = (int64_t)(0u - (uint64_t)stack[sp - 1]);
                pc += 1;
                break;
            case OP_LOAD: {
                if (pc + 1u + 1u > len) FINISH(VM_ERR_OPERAND);
                uint8_t slot = code[pc + 1];
                if (slot >= VM_LOCALS_COUNT) FINISH(VM_ERR_OPERAND);
                if (sp >= VM_STACK_CAPACITY) FINISH(VM_ERR_STACK_OVERFLOW);
                stack[sp++] = locals[slot];
                pc += 2;
                break;
            }
            case OP_STORE: {
                if (pc + 1u + 1u > len) FINISH(VM_ERR_OPERAND);
                uint8_t slot = code[pc + 1];
                if (slot >= VM_LOCALS_COUNT) FINISH(VM_ERR_OPERAND);
                if (sp < 1) FINISH(VM_ERR_STACK_UNDERFLOW);
                locals[slot] = stack[--sp];
                pc += 2;
                break;
            }
            case OP_JMP:
            case OP_JZ:
            case OP_JNZ: {
                if (pc + 1u + 4u > len) FINISH(VM_ERR_OPERAND);
                uint32_t target = 0;
                for (int i = 0; i < 4; i++) target |= (uint32_t)code[pc + 1 + (size_t)i] << (8 * i);
                int do_jump = 1;
                if (op != OP_JMP) {
                    if (sp < 1) FINISH(VM_ERR_STACK_UNDERFLOW);
                    int64_t c = stack[--sp];
                    do_jump = (op == OP_JZ) ? (c == 0) : (c != 0);
                }
                if (do_jump) {
                    if ((size_t)target >= len) FINISH(VM_ERR_BAD_JUMP);
                    pc = target;
                } else {
                    pc += 5;
                }
                break;
            }
            case OP_PRINT: {
                if (sp < 1) FINISH(VM_ERR_STACK_UNDERFLOW);
                int64_t v = stack[--sp];
                if (out != NULL && produced < out_cap) out[produced] = v;
                produced++;
                pc += 1;
                break;
            }
            case OP_HALT:
                FINISH(VM_OK);
            default:
                FINISH(VM_ERR_OPCODE);
        }
    }
#undef FINISH
}
VM_EOF
