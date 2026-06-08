We need a small digital-signal-processing library written from scratch in C. You'll build it over three milestones in `/app/signal.c`, implementing the contract declared in `/app/signal.h`. A non-functional stub is already in `/app/signal.c` for you to replace; do not change `/app/signal.h`. Use only the C standard library and libm (the test build links `-lm` for you).

The test program is linked against every function declared in `/app/signal.h`, so all of them must stay defined at all times. In each milestone, implement that milestone's functions and leave the provided no-op stubs for the remaining functions in place — do not delete a stub, or the build will fail to link.

Your library is compiled together with a separate test program (which you do not have) using `gcc` under UndefinedBehaviorSanitizer, so it must be free of undefined behavior (no misaligned accesses, no invalid pointer arithmetic, no overflow) as well as numerically correct.

Milestone 1: implement `sig_compute_stats`.

Given a real-valued signal `x[0..n)`, fill the `sig_stats` struct with:

- `n` — the number of samples.
- `mean` — the arithmetic mean, `(1/n) * sum(x[j])`.
- `variance` — the **population** variance, `(1/n) * sum((x[j] - mean)^2)` (divide by `n`, not `n-1`).
- `stddev` — `sqrt(variance)`.
- `rms` — the root mean square, `sqrt( (1/n) * sum(x[j]^2) )`.
- `min`, `max` — the smallest and largest sample.

Return `SIG_OK` on success. If `n == 0` or a pointer is NULL, return `SIG_ERR` and do not read the signal. The exact numeric definitions above are checked against an independent recomputation, so the population-vs-sample variance convention matters.
