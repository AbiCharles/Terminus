#!/bin/bash
set -euo pipefail

# Milestone 1 oracle: write the complete reference library to /app/signal.c.
# A single correct implementation (covering time-domain statistics (sig_compute_stats), plus the rest) satisfies this
# milestone and the others, so each milestone's oracle installs the same vetted
# source; the milestone's own verifier exercises the relevant subset.
cat > /app/signal.c <<'SIGNAL_EOF'
#include "signal.h"

#include <math.h>
#include <stddef.h>

/*
 * Reference implementation of the spectral-analysis library.
 *
 * A naive O(n^2) DFT is used (no FFT needed for the sizes exercised here); all
 * conventions match signal.h exactly: population variance, half-spectrum bins
 * 1..n/2 with DC excluded, power-based spectral SNR in decibels, and a 95%
 * normal-approximation confidence interval for the mean.
 */

int sig_compute_stats(const double *x, size_t n, sig_stats *out) {
    if (x == NULL || out == NULL || n == 0) return SIG_ERR;
    double sum = 0.0, sumsq = 0.0;
    double mn = x[0], mx = x[0];
    for (size_t j = 0; j < n; j++) {
        double v = x[j];
        sum += v;
        sumsq += v * v;
        if (v < mn) mn = v;
        if (v > mx) mx = v;
    }
    double mean = sum / (double)n;
    double variance = sumsq / (double)n - mean * mean;
    if (variance < 0.0) variance = 0.0; /* guard tiny negative round-off */
    out->n = n;
    out->mean = mean;
    out->variance = variance;
    out->stddev = sqrt(variance);
    out->rms = sqrt(sumsq / (double)n);
    out->min = mn;
    out->max = mx;
    return SIG_OK;
}

int sig_dft(const double *x, size_t n, sig_complex *out) {
    if (x == NULL || out == NULL || n == 0) return SIG_ERR;
    const double two_pi = 2.0 * acos(-1.0);
    for (size_t k = 0; k < n; k++) {
        double re = 0.0, im = 0.0;
        for (size_t j = 0; j < n; j++) {
            double angle = -two_pi * (double)k * (double)j / (double)n;
            re += x[j] * cos(angle);
            im += x[j] * sin(angle);
        }
        out[k].re = re;
        out[k].im = im;
    }
    return SIG_OK;
}

size_t sig_dominant_bins(const double *x, size_t n, size_t k, size_t *bins) {
    if (x == NULL || bins == NULL || n < 2) return 0;
    size_t half = n / 2;            /* candidate bins are 1..half inclusive */
    size_t avail = half;            /* count of candidate bins              */
    size_t want = k < avail ? k : avail;
    if (want == 0) return 0;

    const double two_pi = 2.0 * acos(-1.0);
    size_t chosen = 0;

    /* Compute half-spectrum powers into a fixed buffer (test sizes are small). */
    enum { CAP = 1 << 15 };
    static double magbuf[CAP];
    size_t lim = half < (size_t)CAP ? half : (size_t)CAP;
    for (size_t m = 1; m <= lim; m++) {
        double re = 0.0, im = 0.0;
        for (size_t j = 0; j < n; j++) {
            double angle = -two_pi * (double)m * (double)j / (double)n;
            re += x[j] * cos(angle);
            im += x[j] * sin(angle);
        }
        magbuf[m - 1] = re * re + im * im; /* compare on power; order matches |.| */
    }

    char used[CAP];
    for (size_t i = 0; i < lim; i++) used[i] = 0;

    while (chosen < want && chosen < lim) {
        size_t best = 0;
        int have = 0;
        double bestpow = -1.0;
        for (size_t i = 0; i < lim; i++) {
            if (used[i]) continue;
            if (!have || magbuf[i] > bestpow) {
                bestpow = magbuf[i];
                best = i;
                have = 1;
            }
        }
        used[best] = 1;
        bins[chosen++] = best + 1; /* bin index (1-based candidate) */
    }
    return chosen;
}

/* Internal helper: total/selected half-spectrum power for SNR. */
static void half_spectrum_power(const double *x, size_t n, size_t k,
                                double *sig_pow, double *noise_pow) {
    const double two_pi = 2.0 * acos(-1.0);
    size_t half = n / 2;
    enum { CAP = 1 << 15 };
    static double magbuf[CAP];
    size_t lim = half < (size_t)CAP ? half : (size_t)CAP;
    for (size_t m = 1; m <= lim; m++) {
        double re = 0.0, im = 0.0;
        for (size_t j = 0; j < n; j++) {
            double angle = -two_pi * (double)m * (double)j / (double)n;
            re += x[j] * cos(angle);
            im += x[j] * sin(angle);
        }
        magbuf[m - 1] = re * re + im * im;
    }
    /* Select the k dominant bins (same rule as sig_dominant_bins). */
    char used[CAP];
    for (size_t i = 0; i < lim; i++) used[i] = 0;
    size_t want = k < lim ? k : lim;
    double sp = 0.0;
    for (size_t c = 0; c < want; c++) {
        size_t best = 0;
        int have = 0;
        double bestpow = -1.0;
        for (size_t i = 0; i < lim; i++) {
            if (used[i]) continue;
            if (!have || magbuf[i] > bestpow) {
                bestpow = magbuf[i];
                best = i;
                have = 1;
            }
        }
        used[best] = 1;
        sp += magbuf[best];
    }
    double np = 0.0;
    for (size_t i = 0; i < lim; i++)
        if (!used[i]) np += magbuf[i];
    *sig_pow = sp;
    *noise_pow = np;
}

double sig_spectral_snr_db(const double *x, size_t n, size_t k) {
    if (x == NULL || n < 2) return 0.0;
    double sp = 0.0, np = 0.0;
    half_spectrum_power(x, n, k, &sp, &np);
    return 10.0 * log10(sp / np);
}

int sig_mean_ci95(const double *x, size_t n, double *lo, double *hi) {
    if (x == NULL || lo == NULL || hi == NULL || n == 0) return SIG_ERR;
    sig_stats s;
    if (sig_compute_stats(x, n, &s) != SIG_OK) return SIG_ERR;
    double se = s.stddev / sqrt((double)n);
    *lo = s.mean - 1.96 * se;
    *hi = s.mean + 1.96 * se;
    return SIG_OK;
}

int sig_accept(const double *x, size_t n, size_t k, double threshold_db) {
    return sig_spectral_snr_db(x, n, k) >= threshold_db ? 1 : 0;
}
SIGNAL_EOF
