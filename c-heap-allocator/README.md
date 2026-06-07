# Fixed-Arena Memory Allocator (C)

Implement a general-purpose dynamic memory allocator in C, from scratch, that
manages a single fixed-size arena. You write your implementation in
`/app/allocator.c` against the contract declared in `/app/allocator.h`. There are
three milestones; each builds on the previous one in the same file.

- **Milestone 1 — Arena allocator.** `xmalloc` and `xfree` over one fixed
  `ALLOC_CAPACITY`-byte arena: every pointer 16-byte aligned, never overlapping a
  live allocation, never exceeding the arena, and returning `NULL` when a request
  cannot be met.
- **Milestone 2 — Reclamation.** Freed blocks are reused, large free regions are
  split to satisfy smaller requests, and `xcalloc` returns zeroed memory while
  rejecting multiplication overflow.
- **Milestone 3 — Coalescing, realloc and statistics.** Adjacent free blocks
  merge so large requests can be satisfied again, `xrealloc` grows/shrinks/relocates
  while preserving contents, and `heap_stats` reports exact live accounting.

Your allocator is compiled together with a hidden test harness under
AddressSanitizer and UndefinedBehaviorSanitizer, so it must be free of memory
errors and undefined behavior in addition to being functionally correct.
