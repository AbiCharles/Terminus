/*
 * Independent verification harness for the bytecode VM.
 *
 * Compiled together with the candidate's vm.c under UndefinedBehaviorSanitizer
 * and run once per scenario (argv[1]). Each scenario assembles a bytecode program
 * with the small emitter below, runs it through vm_run(), and checks the returned
 * status code and the exact sequence of printed values against what the VM's
 * documented semantics require. On success it prints "OK" and exits 0; on any
 * mismatch it prints "FAIL: <reason>" and exits non-zero. A sanitizer abort (for
 * example signed-overflow UB on a naive ADD, or an out-of-bounds program read)
 * also yields a non-zero exit.
 */
#include "vm.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* ---- tiny assembler ---- */

static void emit_op(uint8_t *b, size_t *n, uint8_t op) { b[(*n)++] = op; }

static void emit_push(uint8_t *b, size_t *n, int64_t v) {
    b[(*n)++] = OP_PUSH;
    uint64_t u = (uint64_t)v;
    for (int i = 0; i < 8; i++) b[(*n)++] = (uint8_t)(u >> (8 * i));
}

static void emit_jump(uint8_t *b, size_t *n, uint8_t op, uint32_t target) {
    b[(*n)++] = op;
    for (int i = 0; i < 4; i++) b[(*n)++] = (uint8_t)(target >> (8 * i));
}

static void emit_slot(uint8_t *b, size_t *n, uint8_t op, uint8_t slot) {
    b[(*n)++] = op;
    b[(*n)++] = slot;
}

static void patch_u32(uint8_t *b, size_t pos, uint32_t v) {
    for (int i = 0; i < 4; i++) b[pos + i] = (uint8_t)(v >> (8 * i));
}

/* ---- run + check ---- */

static int64_t g_out[1024];
static size_t g_outlen;

static int run(const uint8_t *code, size_t len) {
    g_outlen = 0;
    return vm_run(code, len, g_out, 1024, &g_outlen);
}

static int expect(int status, int want_status, size_t want_n, const int64_t *want) {
    if (status != want_status) {
        printf("FAIL: status %d, expected %d\n", status, want_status);
        return 1;
    }
    if (g_outlen != want_n) {
        printf("FAIL: produced %zu outputs, expected %zu\n", g_outlen, want_n);
        return 1;
    }
    for (size_t i = 0; i < want_n; i++) {
        if (g_out[i] != want[i]) {
            printf("FAIL: out[%zu]=%lld, expected %lld\n", i, (long long)g_out[i], (long long)want[i]);
            return 1;
        }
    }
    return 0;
}

static uint8_t P[8192];

/* ---- milestone 1: load + stack ops + add/sub + print/halt + errors ---- */

static int sc_push_print(void) {
    size_t n = 0;
    emit_push(P, &n, 42);
    emit_op(P, &n, OP_PRINT);
    emit_push(P, &n, -7);
    emit_op(P, &n, OP_PRINT);
    emit_op(P, &n, OP_HALT);
    int64_t w[2] = {42, -7};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_add_sub(void) {
    size_t n = 0;
    emit_push(P, &n, 10);
    emit_push(P, &n, 3);
    emit_op(P, &n, OP_ADD);
    emit_op(P, &n, OP_PRINT);
    emit_push(P, &n, 10);
    emit_push(P, &n, 3);
    emit_op(P, &n, OP_SUB);
    emit_op(P, &n, OP_PRINT);
    emit_op(P, &n, OP_HALT);
    int64_t w[2] = {13, 7};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_pop(void) {
    size_t n = 0;
    emit_push(P, &n, 1);
    emit_push(P, &n, 99);
    emit_op(P, &n, OP_POP); /* discard the 99 */
    emit_op(P, &n, OP_PRINT); /* prints the remaining 1 */
    emit_op(P, &n, OP_HALT);
    int64_t w[1] = {1};
    return expect(run(P, n), VM_OK, 1, w);
}

static int sc_dup_swap(void) {
    size_t n = 0;
    emit_push(P, &n, 5);
    emit_op(P, &n, OP_DUP);
    emit_op(P, &n, OP_ADD);
    emit_op(P, &n, OP_PRINT); /* 10 */
    emit_push(P, &n, 1);
    emit_push(P, &n, 2);
    emit_op(P, &n, OP_SWAP); /* stack a=2,b=1 */
    emit_op(P, &n, OP_SUB);  /* 2-1 = 1 */
    emit_op(P, &n, OP_PRINT);
    emit_op(P, &n, OP_HALT);
    int64_t w[2] = {10, 1};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_underflow(void) {
    size_t n = 0;
    emit_op(P, &n, OP_ADD); /* nothing on the stack */
    return expect(run(P, n), VM_ERR_STACK_UNDERFLOW, 0, NULL);
}

static int sc_overflow(void) {
    size_t n = 0;
    for (int i = 0; i < (int)VM_STACK_CAPACITY + 1; i++) emit_push(P, &n, i);
    return expect(run(P, n), VM_ERR_STACK_OVERFLOW, 0, NULL);
}

static int sc_bad_opcode(void) {
    size_t n = 0;
    P[n++] = 0x7e; /* not a defined opcode */
    return expect(run(P, n), VM_ERR_OPCODE, 0, NULL);
}

static int sc_truncated(void) {
    size_t n = 0;
    P[n++] = OP_PUSH; /* needs 8 operand bytes; supply only 3 */
    P[n++] = 0x01;
    P[n++] = 0x02;
    P[n++] = 0x03;
    return expect(run(P, n), VM_ERR_OPERAND, 0, NULL);
}

static int sc_no_halt(void) {
    size_t n = 0;
    emit_push(P, &n, 1);
    emit_op(P, &n, OP_PRINT); /* runs off the end with no HALT */
    int64_t w[1] = {1};
    return expect(run(P, n), VM_ERR_NO_HALT, 1, w);
}

/* ---- milestone 2: arithmetic, comparisons, locals ---- */

static int sc_muldivmod(void) {
    size_t n = 0;
    emit_push(P, &n, 7);
    emit_push(P, &n, 6);
    emit_op(P, &n, OP_MUL);
    emit_op(P, &n, OP_PRINT); /* 42 */
    emit_push(P, &n, 20);
    emit_push(P, &n, 6);
    emit_op(P, &n, OP_DIV);
    emit_op(P, &n, OP_PRINT); /* 3 */
    emit_push(P, &n, 20);
    emit_push(P, &n, 6);
    emit_op(P, &n, OP_MOD);
    emit_op(P, &n, OP_PRINT); /* 2 */
    emit_op(P, &n, OP_HALT);
    int64_t w[3] = {42, 3, 2};
    return expect(run(P, n), VM_OK, 3, w);
}

static int sc_div_trunc(void) {
    size_t n = 0;
    emit_push(P, &n, -7);
    emit_push(P, &n, 2);
    emit_op(P, &n, OP_DIV);
    emit_op(P, &n, OP_PRINT); /* -3, truncated toward zero */
    emit_push(P, &n, -7);
    emit_push(P, &n, 2);
    emit_op(P, &n, OP_MOD);
    emit_op(P, &n, OP_PRINT); /* -1 */
    emit_op(P, &n, OP_HALT);
    int64_t w[2] = {-3, -1};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_div_zero(void) {
    size_t n = 0;
    emit_push(P, &n, 5);
    emit_push(P, &n, 0);
    emit_op(P, &n, OP_DIV);
    return expect(run(P, n), VM_ERR_DIV_ZERO, 0, NULL);
}

static int sc_wrapping(void) {
    size_t n = 0;
    emit_push(P, &n, INT64_MAX);
    emit_push(P, &n, 1);
    emit_op(P, &n, OP_ADD);
    emit_op(P, &n, OP_PRINT); /* wraps to INT64_MIN */
    emit_push(P, &n, INT64_MAX);
    emit_push(P, &n, 2);
    emit_op(P, &n, OP_MUL);
    emit_op(P, &n, OP_PRINT); /* (2^63-1)*2 wraps to -2 */
    emit_push(P, &n, INT64_MIN);
    emit_push(P, &n, 1);
    emit_op(P, &n, OP_SUB);
    emit_op(P, &n, OP_PRINT); /* INT64_MIN - 1 wraps to INT64_MAX */
    emit_op(P, &n, OP_HALT);
    int64_t w[3] = {INT64_MIN, -2, INT64_MAX};
    return expect(run(P, n), VM_OK, 3, w);
}

static int sc_div_overflow(void) {
    size_t n = 0;
    emit_push(P, &n, INT64_MIN);
    emit_push(P, &n, -1);
    emit_op(P, &n, OP_DIV);
    emit_op(P, &n, OP_PRINT); /* INT64_MIN / -1 overflows -> wraps to INT64_MIN */
    emit_push(P, &n, INT64_MIN);
    emit_push(P, &n, -1);
    emit_op(P, &n, OP_MOD);
    emit_op(P, &n, OP_PRINT); /* INT64_MIN % -1 = 0 */
    emit_op(P, &n, OP_HALT);
    int64_t w[2] = {INT64_MIN, 0};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_neg(void) {
    size_t n = 0;
    emit_push(P, &n, 5);
    emit_op(P, &n, OP_NEG);
    emit_op(P, &n, OP_PRINT); /* -5 */
    emit_push(P, &n, INT64_MIN);
    emit_op(P, &n, OP_NEG);
    emit_op(P, &n, OP_PRINT); /* -INT64_MIN wraps to INT64_MIN */
    emit_op(P, &n, OP_HALT);
    int64_t w[2] = {-5, INT64_MIN};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_compare(void) {
    size_t n = 0;
    emit_push(P, &n, 3);
    emit_push(P, &n, 5);
    emit_op(P, &n, OP_LT);
    emit_op(P, &n, OP_PRINT); /* 1 */
    emit_push(P, &n, 3);
    emit_push(P, &n, 5);
    emit_op(P, &n, OP_GT);
    emit_op(P, &n, OP_PRINT); /* 0 */
    emit_push(P, &n, 5);
    emit_push(P, &n, 5);
    emit_op(P, &n, OP_EQ);
    emit_op(P, &n, OP_PRINT); /* 1 */
    emit_op(P, &n, OP_HALT);
    int64_t w[3] = {1, 0, 1};
    return expect(run(P, n), VM_OK, 3, w);
}

static int sc_locals(void) {
    size_t n = 0;
    emit_push(P, &n, 11);
    emit_slot(P, &n, OP_STORE, 0);
    emit_push(P, &n, 31);
    emit_slot(P, &n, OP_STORE, 1);
    emit_slot(P, &n, OP_LOAD, 0);
    emit_slot(P, &n, OP_LOAD, 1);
    emit_op(P, &n, OP_ADD);
    emit_op(P, &n, OP_PRINT); /* 42 */
    emit_slot(P, &n, OP_LOAD, 5); /* untouched local defaults to 0 */
    emit_op(P, &n, OP_PRINT);     /* 0 */
    emit_op(P, &n, OP_HALT);
    int64_t w[2] = {42, 0};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_bad_slot(void) {
    size_t n = 0;
    emit_slot(P, &n, OP_LOAD, (uint8_t)VM_LOCALS_COUNT); /* slot 16, out of range */
    return expect(run(P, n), VM_ERR_OPERAND, 0, NULL);
}

/* ---- milestone 3: jumps, conditionals, loops, limits ---- */

static int sc_jmp(void) {
    size_t n = 0;
    emit_push(P, &n, 1);
    emit_op(P, &n, OP_PRINT);
    size_t jpos = n;
    emit_jump(P, &n, OP_JMP, 0); /* target patched below */
    emit_push(P, &n, 999);       /* skipped */
    emit_op(P, &n, OP_PRINT);
    uint32_t target = (uint32_t)n;
    emit_push(P, &n, 2);
    emit_op(P, &n, OP_PRINT);
    emit_op(P, &n, OP_HALT);
    patch_u32(P, jpos + 1, target);
    int64_t w[2] = {1, 2};
    return expect(run(P, n), VM_OK, 2, w);
}

static int sc_conditional(void) {
    /* JZ taken: cond 0 -> skip the 111 print */
    size_t n = 0;
    emit_push(P, &n, 0);
    size_t jpos = n;
    emit_jump(P, &n, OP_JZ, 0);
    emit_push(P, &n, 111);
    emit_op(P, &n, OP_PRINT);
    uint32_t target = (uint32_t)n;
    emit_push(P, &n, 222);
    emit_op(P, &n, OP_PRINT);
    emit_op(P, &n, OP_HALT);
    patch_u32(P, jpos + 1, target);
    int64_t w1[1] = {222};
    if (expect(run(P, n), VM_OK, 1, w1)) return 1;

    /* JNZ not taken: cond 0 -> fall through, print both */
    n = 0;
    emit_push(P, &n, 0);
    jpos = n;
    emit_jump(P, &n, OP_JNZ, 0);
    emit_push(P, &n, 111);
    emit_op(P, &n, OP_PRINT);
    target = (uint32_t)n;
    emit_push(P, &n, 222);
    emit_op(P, &n, OP_PRINT);
    emit_op(P, &n, OP_HALT);
    patch_u32(P, jpos + 1, target);
    int64_t w2[2] = {111, 222};
    return expect(run(P, n), VM_OK, 2, w2);
}

static int sc_loop(void) {
    /* sum 1..5 using locals: slot0 = acc, slot1 = i */
    size_t n = 0;
    emit_push(P, &n, 0);
    emit_slot(P, &n, OP_STORE, 0);
    emit_push(P, &n, 1);
    emit_slot(P, &n, OP_STORE, 1);
    size_t loop = n;
    emit_slot(P, &n, OP_LOAD, 1);
    emit_push(P, &n, 5);
    emit_op(P, &n, OP_GT); /* i > 5 ? */
    size_t jend = n;
    emit_jump(P, &n, OP_JNZ, 0); /* if i>5 goto end */
    emit_slot(P, &n, OP_LOAD, 0);
    emit_slot(P, &n, OP_LOAD, 1);
    emit_op(P, &n, OP_ADD);
    emit_slot(P, &n, OP_STORE, 0); /* acc += i */
    emit_slot(P, &n, OP_LOAD, 1);
    emit_push(P, &n, 1);
    emit_op(P, &n, OP_ADD);
    emit_slot(P, &n, OP_STORE, 1); /* i += 1 */
    emit_jump(P, &n, OP_JMP, (uint32_t)loop);
    uint32_t endaddr = (uint32_t)n;
    emit_slot(P, &n, OP_LOAD, 0);
    emit_op(P, &n, OP_PRINT);
    emit_op(P, &n, OP_HALT);
    patch_u32(P, jend + 1, endaddr);
    int64_t w[1] = {15};
    return expect(run(P, n), VM_OK, 1, w);
}

static int sc_bad_jump(void) {
    size_t n = 0;
    emit_jump(P, &n, OP_JMP, 100000u); /* target far beyond program length */
    return expect(run(P, n), VM_ERR_BAD_JUMP, 0, NULL);
}

static int sc_infinite_loop(void) {
    size_t n = 0;
    emit_jump(P, &n, OP_JMP, 0); /* jump to self forever */
    return expect(run(P, n), VM_ERR_STEP_LIMIT, 0, NULL);
}

struct scenario {
    const char *name;
    int (*fn)(void);
};

static const struct scenario SCENARIOS[] = {
    {"push_print", sc_push_print},
    {"pop", sc_pop},
    {"add_sub", sc_add_sub},
    {"dup_swap", sc_dup_swap},
    {"underflow", sc_underflow},
    {"overflow", sc_overflow},
    {"bad_opcode", sc_bad_opcode},
    {"truncated", sc_truncated},
    {"no_halt", sc_no_halt},
    {"muldivmod", sc_muldivmod},
    {"div_trunc", sc_div_trunc},
    {"div_zero", sc_div_zero},
    {"wrapping", sc_wrapping},
    {"div_overflow", sc_div_overflow},
    {"neg", sc_neg},
    {"compare", sc_compare},
    {"locals", sc_locals},
    {"bad_slot", sc_bad_slot},
    {"jmp", sc_jmp},
    {"conditional", sc_conditional},
    {"loop", sc_loop},
    {"bad_jump", sc_bad_jump},
    {"infinite_loop", sc_infinite_loop},
};

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("FAIL: no scenario given\n");
        return 2;
    }
    for (size_t i = 0; i < sizeof(SCENARIOS) / sizeof(SCENARIOS[0]); i++) {
        if (strcmp(argv[1], SCENARIOS[i].name) == 0) {
            int rc = SCENARIOS[i].fn();
            if (rc == 0) printf("OK\n");
            return rc;
        }
    }
    printf("FAIL: unknown scenario %s\n", argv[1]);
    return 2;
}
