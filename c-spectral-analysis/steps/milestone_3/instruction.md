Finally, add the spectral metrics and the acceptance gate, by extending `/app/signal.c`.

Implement `sig_spectral_snr_db`: the power-based spectral signal-to-noise ratio in decibels over the half spectrum (bins `1..n/2`, DC excluded). Let the **signal power** be the sum of `|out[m]|^2` over the `k` dominant bins (the same bins `sig_dominant_bins` would select), and the **noise power** be the sum of `|out[m]|^2` over the remaining half-spectrum bins. Return

    10 * log10(signal_power / noise_power)

Return `0.0` if `n < 2`. Callers always pass signals with a non-zero noise floor.

Implement `sig_mean_ci95`: the 95% confidence interval for the mean using the normal approximation. With the population standard deviation from milestone 1 and the standard error `se = stddev / sqrt(n)`, set `*lo = mean - 1.96 * se` and `*hi = mean + 1.96 * se`. Return `SIG_OK`, or `SIG_ERR` if `n == 0` or a pointer is NULL.

Implement `sig_accept`: return `1` if `sig_spectral_snr_db(x, n, k) >= threshold_db`, otherwise `0`.

These are checked against an independent reference power computation and the milestone 1 statistics, and the gate must agree with the SNR value it is derived from. The milestone 1 and milestone 2 behaviour must continue to work.
