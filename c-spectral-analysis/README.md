# Spectral-Analysis Library (C)

Implement a small digital-signal-processing library in C, from scratch, using
only the C standard library and libm. You write your implementation in
`/app/signal.c` against the contract declared in `/app/signal.h`. There are three
milestones; each builds on the previous one in the same file.

- **Milestone 1 — Time-domain statistics.** `sig_compute_stats` returns the mean,
  population variance, standard deviation, RMS, minimum and maximum of a signal.
- **Milestone 2 — Spectrum.** `sig_dft` computes the discrete Fourier transform and
  `sig_dominant_bins` returns the dominant frequency bins of the half spectrum.
- **Milestone 3 — Spectral metrics.** `sig_spectral_snr_db` computes the power-based
  spectral signal-to-noise ratio in decibels, `sig_mean_ci95` a 95% confidence
  interval for the mean, and `sig_accept` an SNR-threshold acceptance gate.

Your library is compiled together with a hidden, independent test harness under
UndefinedBehaviorSanitizer, so it must be free of undefined behavior in addition
to being numerically correct. The harness checks your results against direct
recomputation, an independent reference DFT, and analytic spectral invariants
(Parseval's relation, the DC term, and the known content of synthetic tones).
