#ifndef SIGNAL_H
#define SIGNAL_H

#include <stddef.h>

/*
 * Spectral-analysis library contract.
 *
 * You implement every function below in signal.c, from scratch, using only the
 * C standard library (libm is available: link with -lm is handled for you).
 * All signals are real-valued and passed as arrays of `double`. The library is
 * compiled together with a hidden test program under UndefinedBehaviorSanitizer,
 * so it must be free of undefined behavior as well as numerically correct.
 *
 * Return-code convention: functions returning `int` return SIG_OK (0) on success
 * and SIG_ERR (-1) on invalid input (for example n == 0 or a NULL output
 * pointer), leaving outputs unspecified on error.
 */

#define SIG_OK 0
#define SIG_ERR (-1)

/* A complex number used for spectrum values. */
typedef struct {
    double re;
    double im;
} sig_complex;

/* ---- Milestone 1: time-domain statistics ---- */

typedef struct {
    size_t n;        /* number of samples summarised                          */
    double mean;     /* (1/n) * sum(x[j])                                      */
    double variance; /* POPULATION variance: (1/n) * sum((x[j]-mean)^2)        */
    double stddev;   /* sqrt(variance)                                         */
    double rms;      /* sqrt( (1/n) * sum(x[j]^2) )                            */
    double min;      /* smallest sample                                        */
    double max;      /* largest sample                                         */
} sig_stats;

/* Fill `out` with the time-domain statistics of x[0..n). Returns SIG_ERR if
 * n == 0 or x/out is NULL. */
int sig_compute_stats(const double *x, size_t n, sig_stats *out);

/* ---- Milestone 2: discrete Fourier transform and dominant frequencies ---- */

/* Compute the DFT into out[0..n):
 *   out[k] = sum_{j=0}^{n-1} x[j] * ( cos(-2*pi*k*j/n) + i*sin(-2*pi*k*j/n) )
 * `out` must have room for n complex values. Returns SIG_ERR if n == 0 or a
 * pointer is NULL. */
int sig_dft(const double *x, size_t n, sig_complex *out);

/* Identify the dominant frequency bins. Considering only the half spectrum
 * bins m with 1 <= m <= n/2 (DC bin 0 excluded; n/2 is integer division), fill
 * bins[] with the indices of the up-to-k largest magnitudes |out[m]|, ordered
 * by descending magnitude with ties broken by the smaller index. Returns the
 * number of indices written (min(k, n/2)); 0 if n < 2 or a pointer is NULL. */
size_t sig_dominant_bins(const double *x, size_t n, size_t k, size_t *bins);

/* ---- Milestone 3: spectral SNR, confidence interval, acceptance gate ---- */

/* Spectral signal-to-noise ratio in decibels over the half spectrum
 * (bins 1..n/2, DC excluded):
 *   signal_power = sum of |out[m]|^2 over the k dominant bins
 *   noise_power  = sum of |out[m]|^2 over the remaining half-spectrum bins
 *   return 10 * log10(signal_power / noise_power)
 * Returns 0.0 if n < 2; behaviour when noise_power == 0 is unspecified (callers
 * use signals with a non-zero noise floor). */
double sig_spectral_snr_db(const double *x, size_t n, size_t k);

/* 95% confidence interval for the mean using the normal approximation:
 *   se = stddev / sqrt(n)          (stddev is the population stddev above)
 *   *lo = mean - 1.96 * se,  *hi = mean + 1.96 * se
 * Returns SIG_ERR if n == 0 or a pointer is NULL. */
int sig_mean_ci95(const double *x, size_t n, double *lo, double *hi);

/* Acceptance gate: returns 1 if sig_spectral_snr_db(x, n, k) >= threshold_db,
 * else 0. */
int sig_accept(const double *x, size_t n, size_t k, double threshold_db);

#endif /* SIGNAL_H */
