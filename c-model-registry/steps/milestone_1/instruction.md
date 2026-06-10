We need a model-governance registry written from scratch in C — the registry that backs a model-promotion workflow for a credit-default classifier. You'll build it over three milestones in `/app/registry.c`, implementing the contract declared in `/app/registry.h`. A non-functional stub is already in `/app/registry.c` for you to replace; do not change `/app/registry.h`. You manage all memory yourself with `malloc`/`realloc`/`free` — the registry starts empty and grows as model versions are registered. You do **not** train any models: each version's evaluation metrics are given to you.

Your code is compiled together with an independent test harness and run under **UndefinedBehaviorSanitizer** (`-fsanitize=undefined`), so any out-of-bounds access, signed overflow, or other undefined behavior is a hard failure. The harness keeps its own record of what it registered and checks your answers against it, so only exact results pass.

This milestone implements **registration and lookup**: `reg_register`, `reg_version_count`, `reg_get_metrics`, `reg_set_tag`, `reg_get_tag`, and `reg_reset` (read their exact contracts in `registry.h`). The remaining functions (gates, aliases, promotion, rollback, persistence) belong to later milestones — leave them as compiling stubs for now so the file builds.

- Versions of a given model name number from 1 and increment by one per registration; different model names have independent version sequences.
- Tags are per (name, version) string key→value pairs; setting an existing key overwrites it. Tag *values* may be arbitrarily long and contain any non-NUL byte, so store them on the heap (not a fixed buffer).
- `reg_reset` frees all memory and leaves the registry empty and reusable.

The harness registers thousands of models, versions and tags, so keep registration and lookup efficient (a hash map keyed by model name is a good idea) and your nested storage free of leaks and out-of-bounds writes. Compile locally with `gcc -std=c11 -fsanitize=undefined -I/app /app/registry.c your_test.c` to check your work.
