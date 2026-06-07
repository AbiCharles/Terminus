#include "allocator.h"

/*
 * Starting stub for the fixed-arena allocator.
 *
 * Implement the contract declared in allocator.h here. These stubs are
 * intentionally non-functional so the project links before you start.
 */

void *xmalloc(size_t size) {
    (void)size;
    return NULL;
}

void xfree(void *ptr) {
    (void)ptr;
}

void *xrealloc(void *ptr, size_t size) {
    (void)ptr;
    (void)size;
    return NULL;
}

void *xcalloc(size_t nmemb, size_t size) {
    (void)nmemb;
    (void)size;
    return NULL;
}

void heap_stats(heap_stats_t *out) {
    if (out) {
        out->bytes_in_use = 0;
        out->free_bytes = 0;
        out->largest_free_block = 0;
        out->live_allocations = 0;
    }
}
