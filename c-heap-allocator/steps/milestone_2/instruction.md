Now make the allocator reclaim memory, by extending `/app/allocator.c`.

- Freed blocks must be reused. After `xfree`, the space becomes available again so that a long sequence of `xmalloc`/`xfree` calls whose live set always fits in the arena never exhausts it, even when the total number of bytes ever requested far exceeds `ALLOC_CAPACITY`.
- A larger free region must be split to satisfy a smaller request, leaving the remainder available for future allocations rather than wasting it.
- Implement `xcalloc(nmemb, size)`: it returns `nmemb * size` bytes initialized to zero, with the same alignment and non-overlap guarantees as `xmalloc`. It must detect multiplication overflow — if `nmemb * size` would overflow `size_t`, return `NULL` — and otherwise return `NULL` when the request cannot be satisfied.

All of the milestone 1 guarantees (alignment, non-overlap, in-bounds, no corruption of live blocks) still apply to every allocation, including those served from reused or split space. Keep the `xrealloc` and `heap_stats` stubs in place — the build still links every function in the header.
