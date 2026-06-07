#ifndef ALLOCATOR_H
#define ALLOCATOR_H

#include <stddef.h>

/*
 * Fixed-arena allocator contract.
 *
 * Your allocator manages ONE region of exactly ALLOC_CAPACITY bytes that it
 * obtains a single time (lazily, on first use is fine) and never grows: it must
 * never request more memory from the operating system afterwards. Every pointer
 * returned to the caller must be aligned to ALLOC_ALIGNMENT bytes.
 *
 * All sizes below are expressed in bytes and refer to the caller-visible
 * payload (the number of usable bytes the caller asked for), never to any
 * internal bookkeeping/overhead your implementation adds.
 */

#define ALLOC_CAPACITY ((size_t)1u << 20) /* 1 MiB managed arena */
#define ALLOC_ALIGNMENT ((size_t)16u)     /* every returned pointer is 16-byte aligned */

/* Allocate `size` payload bytes, 16-byte aligned, not overlapping any other
 * live allocation. Returns NULL when the request cannot be satisfied.
 * xmalloc(0) returns NULL. */
void *xmalloc(size_t size);

/* Release a block previously returned by xmalloc/xrealloc/xcalloc, making its
 * space available again. xfree(NULL) is a no-op. */
void xfree(void *ptr);

/* Resize the allocation at `ptr` to `size` payload bytes, preserving the first
 * min(old_size, size) bytes of its contents. xrealloc(NULL, size) behaves like
 * xmalloc(size); xrealloc(ptr, 0) frees ptr and returns NULL. Returns NULL
 * (leaving the original block intact) if a non-zero request cannot be met. */
void *xrealloc(void *ptr, size_t size);

/* Allocate nmemb*size zeroed payload bytes. Returns NULL on multiplication
 * overflow or when the request cannot be satisfied. */
void *xcalloc(size_t nmemb, size_t size);

/* Snapshot of the arena. `bytes_in_use` is the sum of the payload sizes
 * (the exact values passed to xmalloc/xrealloc/xcalloc) of all currently-live
 * allocations. `free_bytes` is the total payload space available for future
 * allocations. `largest_free_block` is the payload size of the single largest
 * allocation that could currently be satisfied. `live_allocations` is the count
 * of outstanding allocations. */
typedef struct {
    size_t bytes_in_use;
    size_t free_bytes;
    size_t largest_free_block;
    size_t live_allocations;
} heap_stats_t;

void heap_stats(heap_stats_t *out);

#endif /* ALLOCATOR_H */
