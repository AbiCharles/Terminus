#include "vm.h"

/*
 * Starting stub for the bytecode virtual machine.
 *
 * Implement the contract declared in vm.h here. This stub is intentionally
 * non-functional so the project links before you start.
 */

int vm_run(const uint8_t *code, size_t len, int64_t *out, size_t out_cap, size_t *out_len) {
    (void)code;
    (void)len;
    (void)out;
    (void)out_cap;
    if (out_len) *out_len = 0;
    return VM_ERR_NO_HALT;
}
