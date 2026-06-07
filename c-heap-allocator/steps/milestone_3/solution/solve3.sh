#!/bin/bash
set -euo pipefail

# Milestone 3 oracle: write the complete reference allocator to /app/allocator.c.
# A single correct implementation (coalescing, xrealloc, and heap_stats completing the allocator)
# satisfies this milestone and the others, so each milestone's oracle installs the
# same vetted source; the milestone's own verifier exercises the relevant subset.
cat > /app/allocator.c <<'ALLOCATOR_EOF'
#include "allocator.h"

#include <stdint.h>
#include <string.h>

/*
 * Reference allocator: a single fixed arena managed as an address-ordered
 * implicit list of blocks. Each block carries a 16-byte header { size, req }
 * immediately before its payload, so payloads stay 16-byte aligned. A block is
 * free iff req == FREE. Adjacent free blocks are merged by a forward coalescing
 * pass run before each allocation and before reporting stats.
 */

#define FREE ((size_t)-1)

typedef struct block {
    size_t size; /* payload capacity in bytes, always a multiple of 16 */
    size_t req;  /* requested payload bytes if live; FREE if available */
} block_t;

static unsigned char g_arena[ALLOC_CAPACITY] __attribute__((aligned(16)));
static int g_init = 0;

static size_t round_up(size_t n, size_t a) { return (n + a - 1) & ~(a - 1); }

static block_t *arena_first(void) { return (block_t *)g_arena; }
static unsigned char *arena_end(void) { return g_arena + ALLOC_CAPACITY; }

static block_t *block_next(block_t *b) {
    return (block_t *)((unsigned char *)b + sizeof(block_t) + b->size);
}
static void *block_payload(block_t *b) { return (unsigned char *)b + sizeof(block_t); }
static block_t *payload_block(void *p) {
    return (block_t *)((unsigned char *)p - sizeof(block_t));
}

static void alloc_init(void) {
    block_t *b = arena_first();
    b->size = ALLOC_CAPACITY - sizeof(block_t);
    b->req = FREE;
    g_init = 1;
}

static void coalesce_all(void) {
    block_t *b = arena_first();
    while ((unsigned char *)b < arena_end()) {
        if (b->req == FREE) {
            block_t *n = block_next(b);
            while ((unsigned char *)n < arena_end() && n->req == FREE) {
                b->size += sizeof(block_t) + n->size;
                n = block_next(b);
            }
        }
        b = block_next(b);
    }
}

/* Carve `asize` payload bytes out of a free block, splitting off the remainder
 * as a new free block when it is large enough to be useful. */
static void place(block_t *b, size_t asize, size_t req) {
    if (b->size >= asize + sizeof(block_t) + ALLOC_ALIGNMENT) {
        block_t *rem = (block_t *)((unsigned char *)b + sizeof(block_t) + asize);
        rem->size = b->size - asize - sizeof(block_t);
        rem->req = FREE;
        b->size = asize;
    }
    b->req = req;
}

void *xmalloc(size_t size) {
    if (!g_init) alloc_init();
    if (size == 0) return NULL;
    size_t asize = round_up(size, ALLOC_ALIGNMENT);
    coalesce_all();
    for (block_t *b = arena_first(); (unsigned char *)b < arena_end(); b = block_next(b)) {
        if (b->req == FREE && b->size >= asize) {
            place(b, asize, size);
            return block_payload(b);
        }
    }
    return NULL;
}

void xfree(void *ptr) {
    if (ptr == NULL) return;
    payload_block(ptr)->req = FREE;
}

void *xcalloc(size_t nmemb, size_t size) {
    if (nmemb != 0 && size > ((size_t)-1) / nmemb) return NULL;
    size_t total = nmemb * size;
    void *p = xmalloc(total);
    if (p != NULL) memset(p, 0, total);
    return p;
}

void *xrealloc(void *ptr, size_t size) {
    if (ptr == NULL) return xmalloc(size);
    if (size == 0) {
        xfree(ptr);
        return NULL;
    }
    block_t *b = payload_block(ptr);
    size_t old_req = b->req;
    size_t asize = round_up(size, ALLOC_ALIGNMENT);

    if (b->size >= asize) { /* shrink (or exact) in place */
        place(b, asize, size);
        return ptr;
    }

    /* Try to grow in place by absorbing immediately-following free blocks. */
    block_t *n = block_next(b);
    while ((unsigned char *)n < arena_end() && n->req == FREE && b->size < asize) {
        b->size += sizeof(block_t) + n->size;
        n = block_next(b);
    }
    if (b->size >= asize) {
        place(b, asize, size);
        return ptr;
    }

    /* Relocate. The original block keeps its data until the copy is done. */
    void *np = xmalloc(size);
    if (np == NULL) return NULL;
    size_t copy = old_req < size ? old_req : size;
    memcpy(np, ptr, copy);
    xfree(ptr);
    return np;
}

void heap_stats(heap_stats_t *out) {
    if (!g_init) alloc_init();
    if (out == NULL) return;
    coalesce_all();
    size_t in_use = 0, freeb = 0, largest = 0, live = 0;
    for (block_t *b = arena_first(); (unsigned char *)b < arena_end(); b = block_next(b)) {
        if (b->req == FREE) {
            freeb += b->size;
            if (b->size > largest) largest = b->size;
        } else {
            in_use += b->req;
            live += 1;
        }
    }
    out->bytes_in_use = in_use;
    out->free_bytes = freeb;
    out->largest_free_block = largest;
    out->live_allocations = live;
}
ALLOCATOR_EOF
