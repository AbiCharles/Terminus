#ifndef VM_H
#define VM_H

#include <stddef.h>
#include <stdint.h>

/*
 * Stack-based bytecode virtual machine contract.
 *
 * You implement vm_run() in vm.c, from scratch, using only the C standard
 * library. The VM executes a flat little-endian bytecode program over a stack
 * of signed 64-bit integers. It is compiled together with a hidden test program
 * under UndefinedBehaviorSanitizer, so it must be free of undefined behavior
 * (no out-of-bounds reads of the program, no signed-integer-overflow UB) as well
 * as functionally correct.
 */

/* Limits. */
#define VM_STACK_CAPACITY 256u    /* maximum operand-stack depth                 */
#define VM_LOCALS_COUNT 16u       /* addressable local slots, indices 0..15      */
#define VM_MAX_STEPS 1000000u     /* instruction budget; exceeding it is an error */

/* Status codes returned by vm_run(). */
#define VM_OK 0                   /* program executed an explicit HALT            */
#define VM_ERR_OPCODE 1           /* an undefined opcode byte was encountered     */
#define VM_ERR_OPERAND 2          /* an operand ran past the program OR is out of
                                     range (a local slot >= VM_LOCALS_COUNT)      */
#define VM_ERR_STACK_OVERFLOW 3   /* a push would exceed VM_STACK_CAPACITY        */
#define VM_ERR_STACK_UNDERFLOW 4  /* an op needed more operands than were on stack*/
#define VM_ERR_DIV_ZERO 5         /* DIV or MOD with a zero divisor               */
#define VM_ERR_BAD_JUMP 6         /* a jump target was outside [0, len)           */
#define VM_ERR_NO_HALT 7          /* control reached the program's end, no HALT   */
#define VM_ERR_STEP_LIMIT 8       /* executed more than VM_MAX_STEPS instructions */

/*
 * Opcodes. Operands are immediate, little-endian, and follow the opcode byte.
 * Arithmetic is on int64_t with two's-complement WRAPPING (no trapping/UB).
 * Binary ops pop b then a (b is the value pushed most recently) and push the
 * result of "a OP b". Comparisons push 1 for true, 0 for false.
 */
#define OP_PUSH 0x01  /* + int64 (8 bytes LE): push the constant                  */
#define OP_POP 0x02   /* discard top                                              */
#define OP_DUP 0x03   /* push a copy of top                                       */
#define OP_SWAP 0x04  /* swap the top two values                                  */
#define OP_ADD 0x10   /* push a + b (wrapping)                                    */
#define OP_SUB 0x11   /* push a - b (wrapping)                                    */
#define OP_MUL 0x12   /* push a * b (wrapping)                                    */
#define OP_DIV 0x13   /* push a / b, truncated toward zero; b==0 -> VM_ERR_DIV_ZERO*/
#define OP_MOD 0x14   /* push a % b (C truncated remainder); b==0 -> VM_ERR_DIV_ZERO*/
#define OP_NEG 0x15   /* push -a (wrapping)                                       */
#define OP_LT 0x20    /* push (a < b) ? 1 : 0                                     */
#define OP_EQ 0x21    /* push (a == b) ? 1 : 0                                    */
#define OP_GT 0x22    /* push (a > b) ? 1 : 0                                     */
#define OP_LOAD 0x50  /* + uint8 slot: push locals[slot] (every local starts 0)   */
#define OP_STORE 0x51 /* + uint8 slot: pop top into locals[slot]                  */
#define OP_JMP 0x30   /* + uint32 (4 bytes LE): set pc to the target address      */
#define OP_JZ 0x31    /* + uint32: pop c; if c == 0 set pc to target             */
#define OP_JNZ 0x32   /* + uint32: pop c; if c != 0 set pc to target             */
#define OP_PRINT 0x40 /* pop a; append it to the output                          */
#define OP_HALT 0xff  /* stop and return VM_OK                                    */

/*
 * Execute `code[0..len)` starting at program counter 0.
 *
 * Each OP_PRINT pops a value and appends it to `out` (up to `out_cap` values);
 * `*out_len` is set to the number of values produced. Execution stops at the
 * first OP_HALT (returning VM_OK) or at the first error (returning that error's
 * status code). A divisor of zero, an out-of-range jump, a stack overflow or
 * underflow, an undefined opcode, an operand that extends past the end of the
 * program, reaching the end without a HALT, and exceeding VM_MAX_STEPS are all
 * errors with the corresponding VM_ERR_* code. `code` may be NULL only if
 * `len == 0` (which yields VM_ERR_NO_HALT).
 */
int vm_run(const uint8_t *code, size_t len, int64_t *out, size_t out_cap, size_t *out_len);

#endif /* VM_H */
