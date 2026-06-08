/*
 * Independent verification harness for the spectral-analysis library.
 *
 * Compiled together with the candidate's signal.c under UndefinedBehaviorSanitizer
 * and run once per scenario (argv[1]). Each scenario builds deterministic signals,
 * calls the candidate's functions, and checks the results against independently
 * computed references: direct summations for the time-domain statistics, an
 * independent reference DFT and the analytic invariants (Parseval's relation, the
 * DC term, and the known spectral content of synthetic sinusoids) for the spectrum,
 * and a reference power computation for the spectral SNR. On success it prints "OK"
 * and exits 0; on any mismatch it prints "FAIL: <reason>" and exits non-zero.
 */
#include "signal.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#define MAXN 4096

static int fail(const char *msg) {
    printf("FAIL: %s\n", msg);
    return 1;
}

static int fail2(const char *msg, double a, double b) {
    printf("FAIL: %s (got %.12g, expected %.12g)\n", msg, a, b);
    return 1;
}

/* Absolute+relative closeness. */
static int close_tol(double a, double b, double tol) {
    return fabs(a - b) <= tol * (1.0 + fabs(b));
}

/* Deterministic PRNG so workloads are identical on every platform/run. */
static unsigned long g_rng = 0x2545f4914f6cdd1dUL;
static double uniform(void) {
    g_rng = g_rng * 6364136223846793005UL + 1442695040888963407UL;
    /* top 53 bits -> [0,1) -> map to [-1,1) */
    double u = (double)(g_rng >> 11) / 9007199254740992.0;
    return 2.0 * u - 1.0;
}
static void reseed(void) { g_rng = 0x2545f4914f6cdd1dUL; }

static const double PI = 3.14159265358979323846;

/* Independent reference DFT. */
static void ref_dft(const double *x, size_t n, double *re, double *im) {
    for (size_t k = 0; k < n; k++) {
        double r = 0.0, i = 0.0;
        for (size_t j = 0; j < n; j++) {
            double a = -2.0 * PI * (double)k * (double)j / (double)n;
            r += x[j] * cos(a);
            i += x[j] * sin(a);
        }
        re[k] = r;
        im[k] = i;
    }
}

/* ---- milestone 1: time-domain statistics ---- */

static int sc_stats_known(void) {
    double x[5] = {1.0, 2.0, 3.0, 4.0, 5.0};
    sig_stats s;
    if (sig_compute_stats(x, 5, &s) != SIG_OK) return fail("sig_compute_stats returned error on valid input");
    if (s.n != 5) return fail("stats.n is wrong");
    if (!close_tol(s.mean, 3.0, 1e-12)) return fail2("mean", s.mean, 3.0);
    if (!close_tol(s.variance, 2.0, 1e-12)) return fail2("population variance", s.variance, 2.0);
    if (!close_tol(s.stddev, sqrt(2.0), 1e-12)) return fail2("stddev", s.stddev, sqrt(2.0));
    if (!close_tol(s.rms, sqrt(11.0), 1e-12)) return fail2("rms", s.rms, sqrt(11.0));
    if (!close_tol(s.min, 1.0, 1e-12)) return fail2("min", s.min, 1.0);
    if (!close_tol(s.max, 5.0, 1e-12)) return fail2("max", s.max, 5.0);
    return 0;
}

static int sc_stats_random(void) {
    static double x[MAXN];
    size_t n = 1000;
    reseed();
    double sum = 0.0, sumsq = 0.0, mn, mx;
    for (size_t j = 0; j < n; j++) {
        x[j] = 5.0 * uniform() + 0.3;
        sum += x[j];
        sumsq += x[j] * x[j];
        if (j == 0 || x[j] < mn) mn = x[j];
        if (j == 0 || x[j] > mx) mx = x[j];
    }
    double mean = sum / (double)n;
    double var = sumsq / (double)n - mean * mean;
    sig_stats s;
    if (sig_compute_stats(x, n, &s) != SIG_OK) return fail("sig_compute_stats returned error");
    if (!close_tol(s.mean, mean, 1e-9)) return fail2("mean", s.mean, mean);
    if (!close_tol(s.variance, var, 1e-9)) return fail2("variance", s.variance, var);
    if (!close_tol(s.stddev, sqrt(var), 1e-9)) return fail2("stddev", s.stddev, sqrt(var));
    if (!close_tol(s.rms, sqrt(sumsq / (double)n), 1e-9)) return fail2("rms", s.rms, sqrt(sumsq / (double)n));
    if (!close_tol(s.min, mn, 1e-12)) return fail2("min", s.min, mn);
    if (!close_tol(s.max, mx, 1e-12)) return fail2("max", s.max, mx);
    return 0;
}

static int sc_stats_edge(void) {
    double x[1] = {7.5};
    sig_stats s;
    if (sig_compute_stats(x, 0, &s) != SIG_ERR) return fail("n==0 must return SIG_ERR");
    if (sig_compute_stats(x, 1, &s) != SIG_OK) return fail("n==1 must succeed");
    if (!close_tol(s.mean, 7.5, 1e-12) || !close_tol(s.variance, 0.0, 1e-12) ||
        !close_tol(s.rms, 7.5, 1e-12) || !close_tol(s.min, 7.5, 1e-12) || !close_tol(s.max, 7.5, 1e-12))
        return fail("single-sample statistics are wrong");
    return 0;
}

/* ---- milestone 2: DFT and dominant frequencies ---- */

static int sc_dft_dc_parseval(void) {
    static double x[MAXN];
    static sig_complex X[MAXN];
    size_t n = 256;
    reseed();
    double sum = 0.0, energy = 0.0;
    for (size_t j = 0; j < n; j++) {
        x[j] = 3.0 * uniform() - 0.4;
        sum += x[j];
        energy += x[j] * x[j];
    }
    if (sig_dft(x, n, X) != SIG_OK) return fail("sig_dft returned error");
    if (!close_tol(X[0].re, sum, 1e-6)) return fail2("DC term real part", X[0].re, sum);
    if (fabs(X[0].im) > 1e-6 * (1.0 + fabs(sum))) return fail("DC term imaginary part should be ~0");
    double spec = 0.0;
    for (size_t k = 0; k < n; k++) spec += X[k].re * X[k].re + X[k].im * X[k].im;
    if (!close_tol(spec, (double)n * energy, 1e-6))
        return fail2("Parseval sum(|X|^2) vs n*sum(x^2)", spec, (double)n * energy);
    return 0;
}

static int sc_dft_reference(void) {
    static double x[MAXN];
    static sig_complex X[MAXN];
    static double re[MAXN], im[MAXN];
    size_t n = 128;
    reseed();
    for (size_t j = 0; j < n; j++) x[j] = uniform();
    if (sig_dft(x, n, X) != SIG_OK) return fail("sig_dft returned error");
    ref_dft(x, n, re, im);
    size_t probes[6] = {0, 1, 7, 50, 63, 127};
    for (int p = 0; p < 6; p++) {
        size_t k = probes[p];
        if (!close_tol(X[k].re, re[k], 1e-6)) return fail2("DFT real part vs reference", X[k].re, re[k]);
        if (!close_tol(X[k].im, im[k], 1e-6)) return fail2("DFT imag part vs reference", X[k].im, im[k]);
    }
    return 0;
}

static int sc_dominant_bins(void) {
    static double x[MAXN];
    static sig_complex X[MAXN];
    size_t n = 256;
    size_t f1 = 10, f2 = 37, f3 = 80;
    double a1 = 2.0, a2 = 1.0, a3 = 0.5;
    for (size_t j = 0; j < n; j++) {
        double t = (double)j;
        x[j] = a1 * sin(2.0 * PI * (double)f1 * t / (double)n) +
               a2 * sin(2.0 * PI * (double)f2 * t / (double)n) +
               a3 * sin(2.0 * PI * (double)f3 * t / (double)n);
    }
    static size_t bins[MAXN];
    size_t got = sig_dominant_bins(x, n, 3, bins);
    if (got != 3) return fail("sig_dominant_bins should return 3 indices");
    if (bins[0] != f1 || bins[1] != f2 || bins[2] != f3)
        return fail("dominant bins are not the expected [10,37,80] by descending amplitude");
    /* peak magnitude of a pure sine of amplitude A is n*A/2 at its bin */
    if (sig_dft(x, n, X) != SIG_OK) return fail("sig_dft returned error");
    double m1 = sqrt(X[f1].re * X[f1].re + X[f1].im * X[f1].im);
    if (!close_tol(m1, (double)n * a1 / 2.0, 1e-6)) return fail2("peak magnitude at f1", m1, (double)n * a1 / 2.0);
    /* k larger than available still returns at most n/2 distinct bins */
    size_t many = sig_dominant_bins(x, n, 1000, bins);
    if (many != n / 2) return fail("dominant bins with large k must return n/2 indices");
    return 0;
}

/* ---- milestone 3: spectral SNR, confidence interval, gate ---- */

static void make_signal_plus_noise(double *x, size_t n, size_t f, double amp, double noise) {
    reseed();
    for (size_t j = 0; j < n; j++)
        x[j] = amp * sin(2.0 * PI * (double)f * (double)j / (double)n) + noise * uniform();
}

static double ref_snr_db(const double *x, size_t n, size_t k) {
    static double re[MAXN], im[MAXN];
    ref_dft(x, n, re, im);
    size_t half = n / 2;
    static double pow_[MAXN];
    for (size_t m = 1; m <= half; m++) pow_[m - 1] = re[m] * re[m] + im[m] * im[m];
    char used[MAXN];
    for (size_t i = 0; i < half; i++) used[i] = 0;
    size_t want = k < half ? k : half;
    double sp = 0.0;
    for (size_t c = 0; c < want; c++) {
        size_t best = 0;
        int have = 0;
        double bp = -1.0;
        for (size_t i = 0; i < half; i++) {
            if (used[i]) continue;
            if (!have || pow_[i] > bp) { bp = pow_[i]; best = i; have = 1; }
        }
        used[best] = 1;
        sp += pow_[best];
    }
    double np = 0.0;
    for (size_t i = 0; i < half; i++) if (!used[i]) np += pow_[i];
    return 10.0 * log10(sp / np);
}

static int sc_snr_value(void) {
    static double x[MAXN];
    size_t n = 512;
    make_signal_plus_noise(x, n, 20, 2.0, 0.05);
    for (size_t k = 1; k <= 3; k++) {
        double got = sig_spectral_snr_db(x, n, k);
        double ref = ref_snr_db(x, n, k);
        if (!close_tol(got, ref, 1e-6)) return fail2("spectral SNR (dB)", got, ref);
    }
    return 0;
}

static int sc_snr_ordering(void) {
    static double xs[MAXN], xn[MAXN];
    size_t n = 512;
    make_signal_plus_noise(xs, n, 20, 2.0, 0.02);  /* strong tone */
    reseed();
    for (size_t j = 0; j < n; j++) xn[j] = 0.5 * uniform(); /* noise only */
    double snr_sig = sig_spectral_snr_db(xs, n, 1);
    double snr_noise = sig_spectral_snr_db(xn, n, 1);
    if (!(snr_sig > snr_noise + 10.0))
        return fail("a strong tone must have markedly higher spectral SNR than noise");
    return 0;
}

static int sc_ci(void) {
    static double x[MAXN];
    size_t n = 400;
    reseed();
    for (size_t j = 0; j < n; j++) x[j] = 2.0 * uniform() + 1.0;
    sig_stats s;
    if (sig_compute_stats(x, n, &s) != SIG_OK) return fail("stats failed");
    double se = s.stddev / sqrt((double)n);
    double elo = s.mean - 1.96 * se, ehi = s.mean + 1.96 * se;
    double lo, hi;
    if (sig_mean_ci95(x, n, &lo, &hi) != SIG_OK) return fail("sig_mean_ci95 returned error");
    if (!close_tol(lo, elo, 1e-9)) return fail2("CI lower bound", lo, elo);
    if (!close_tol(hi, ehi, 1e-9)) return fail2("CI upper bound", hi, ehi);
    if (sig_mean_ci95(x, 0, &lo, &hi) != SIG_ERR) return fail("n==0 CI must return SIG_ERR");
    return 0;
}

static int sc_gate(void) {
    static double xs[MAXN], xn[MAXN];
    size_t n = 512;
    make_signal_plus_noise(xs, n, 20, 2.0, 0.02);
    reseed();
    for (size_t j = 0; j < n; j++) xn[j] = 0.5 * uniform();
    double thr = 10.0;
    if (sig_accept(xs, n, 1, thr) != 1) return fail("strong-tone signal must be accepted at 10 dB");
    if (sig_accept(xn, n, 1, thr) != 0) return fail("noise-only signal must be rejected at 10 dB");
    /* gate is consistent with the SNR value */
    int expect = sig_spectral_snr_db(xs, n, 1) >= thr ? 1 : 0;
    if (sig_accept(xs, n, 1, thr) != expect) return fail("sig_accept inconsistent with sig_spectral_snr_db");
    return 0;
}

struct scenario {
    const char *name;
    int (*fn)(void);
};

static const struct scenario SCENARIOS[] = {
    {"stats_known", sc_stats_known},
    {"stats_random", sc_stats_random},
    {"stats_edge", sc_stats_edge},
    {"dft_dc_parseval", sc_dft_dc_parseval},
    {"dft_reference", sc_dft_reference},
    {"dominant_bins", sc_dominant_bins},
    {"snr_value", sc_snr_value},
    {"snr_ordering", sc_snr_ordering},
    {"ci", sc_ci},
    {"gate", sc_gate},
};

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("FAIL: no scenario given\n");
        return 2;
    }
    for (size_t i = 0; i < sizeof(SCENARIOS) / sizeof(SCENARIOS[0]); i++) {
        if (strcmp(argv[1], SCENARIOS[i].name) == 0) {
            int rc = SCENARIOS[i].fn();
            if (rc == 0) printf("OK\n");
            return rc;
        }
    }
    printf("FAIL: unknown scenario %s\n", argv[1]);
    return 2;
}
