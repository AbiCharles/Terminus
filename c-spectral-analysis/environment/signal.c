#include "signal.h"

/*
 * Starting stub for the spectral-analysis library.
 *
 * Implement the contract declared in signal.h here. These stubs are
 * intentionally non-functional so the project links before you start.
 */

int sig_compute_stats(const double *x, size_t n, sig_stats *out) {
    (void)x;
    (void)n;
    (void)out;
    return SIG_ERR;
}

int sig_dft(const double *x, size_t n, sig_complex *out) {
    (void)x;
    (void)n;
    (void)out;
    return SIG_ERR;
}

size_t sig_dominant_bins(const double *x, size_t n, size_t k, size_t *bins) {
    (void)x;
    (void)n;
    (void)k;
    (void)bins;
    return 0;
}

double sig_spectral_snr_db(const double *x, size_t n, size_t k) {
    (void)x;
    (void)n;
    (void)k;
    return 0.0;
}

int sig_mean_ci95(const double *x, size_t n, double *lo, double *hi) {
    (void)x;
    (void)n;
    (void)lo;
    (void)hi;
    return SIG_ERR;
}

int sig_accept(const double *x, size_t n, size_t k, double threshold_db) {
    (void)x;
    (void)n;
    (void)k;
    (void)threshold_db;
    return 0;
}
