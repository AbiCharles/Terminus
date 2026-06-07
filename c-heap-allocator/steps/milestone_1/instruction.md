We need a general-purpose memory allocator written from scratch in C. You'll build it over three milestones in `/app/allocator.c`, implementing the contract declared in `/app/allocator.h`. A non-functional stub is already in `/app/allocator.c` for you to replace; do not change `/app/allocator.h`.

Your allocator manages a single fixed region of exactly `ALLOC_CAPACITY` bytes that it obtains once and never grows — it must never ask the operating system for more memory after that. It will be compiled together with a separate test program (which you do not have) using `gcc` under AddressSanitizer and UndefinedBehaviorSanitizer, so it must be completely free of memory errors and undefined behavior as well as functionally correct.

Milestone 1: implement `xmalloc` and `xfree`.

- `xmalloc(size)` returns a pointer to at least `size` usable bytes, aligned to `ALLOC_ALIGNMENT` bytes, that does not overlap any other currently-live allocation and lies within the arena. It returns `NULL` when the request cannot be satisfied from the remaining space, and `xmalloc(0)` returns `NULL`.
- `xfree(ptr)` releases a block previously returned by `xmalloc`. `xfree(NULL)` is a no-op.

The data in a live allocation must never be disturbed by later `xmalloc`/`xfree` calls on other blocks. You do not yet need to reclaim freed space for reuse in this milestone — that comes next — but freeing must never corrupt other live blocks, and the arena must report exhaustion by returning `NULL` rather than handing back overlapping or out-of-bounds memory.
