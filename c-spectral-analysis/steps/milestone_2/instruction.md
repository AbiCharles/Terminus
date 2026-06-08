Now add the frequency-domain analysis, by extending `/app/signal.c`.

Implement `sig_dft`: compute the discrete Fourier transform of `x[0..n)` into the caller-provided `out[0..n)`, using exactly the convention

    out[k] = sum_{j=0}^{n-1} x[j] * ( cos(-2*pi*k*j/n) + i*sin(-2*pi*k*j/n) )

for each `k` in `[0, n)`, where `out[k].re` and `out[k].im` are the real and imaginary parts. Return `SIG_OK`, or `SIG_ERR` if `n == 0` or a pointer is NULL. (A direct O(n^2) transform is fine; no fast-Fourier-transform is required.)

Implement `sig_dominant_bins`: identify the strongest frequency components. Considering only the half-spectrum bins `m` with `1 <= m <= n/2` (the DC bin 0 is excluded; `n/2` is integer division), write into `bins[]` the indices of the up-to-`k` largest magnitudes `|out[m]|`, ordered by **descending magnitude**, breaking ties in favour of the **smaller index**. Return the number of indices written, which is `min(k, n/2)`; return 0 if `n < 2` or a pointer is NULL.

Both functions are checked against an independent reference DFT and the analytic spectral invariants (Parseval's relation, the DC term equalling the sample sum, and the known bins and peak magnitudes of synthetic sinusoids), so the transform convention and the dominant-bin ordering must match exactly. The milestone 1 statistics must continue to work, and the milestone 3 functions must stay defined — keep their no-op stubs in place so the build still links.
