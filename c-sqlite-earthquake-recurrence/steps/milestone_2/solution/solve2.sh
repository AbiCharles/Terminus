#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: self-contained — (re)write the full earthquake CLI to
# /app/quake.c, compile it against libsqlite3, and exercise the `stats` subcommand.
# Self-contained so this milestone's oracle works whether or not milestone 1 ran
# first in the same container.
cat > /app/quake.c <<'QUAKE_EOF'
/* Earthquake recurrence analyzer.
 *
 * A SQLite-backed CLI that filters an earthquake catalog by region (named
 * region and/or a lat/lon bounding box), date range, depth and magnitude, then
 * computes the magnitude of completeness (Mc) by the Wiemer & Wyss (2000)
 * goodness-of-fit test, the Gutenberg-Richter b-value by the Aki-Utsu maximum
 * likelihood estimator (with the Shi & Bolt 1982 uncertainty), and Poisson
 * exceedance probabilities. All data is read through SQLite queries; the tool
 * emits deterministic CSV and JSON and exits nonzero on invalid filters
 * (status 2) or insufficient sample sizes (status 3).
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sqlite3.h>

#define DELTA_M 0.1
#define GFT_CONFIDENCE 90.0
#define MIN_SAMPLE 30      /* minimum events at/above Mc for a stable fit */
#define MIN_BINS_ABOVE_MC 4 /* minimum filled magnitude bins spanned */
#define EX_OK 0
#define EX_BADFILTER 2
#define EX_INSUFFICIENT 3

/* ---- filter specification -------------------------------------------------- */
typedef struct {
    const char *db_path;
    const char *region;          /* named region, or NULL */
    int has_lat_min, has_lat_max, has_lon_min, has_lon_max;
    double lat_min, lat_max, lon_min, lon_max;
    const char *start, *end;     /* ISO 8601 strings, or NULL */
    int has_depth_min, has_depth_max, has_mag_min, has_mag_max;
    double depth_min, depth_max, mag_min, mag_max;
    const char *out;             /* --out path */
    const char *out_prefix;      /* --out-prefix path */
    const char *targets;         /* comma list, or NULL */
    double window_years;
    int has_window;
} Filters;

static void die_usage(const char *msg) {
    fprintf(stderr, "error: %s\n", msg);
    exit(EX_BADFILTER);
}

static double parse_double_or_die(const char *s, const char *flag) {
    char *endp = NULL;
    double v = strtod(s, &endp);
    if (endp == s || *endp != '\0') {
        fprintf(stderr, "error: %s expects a number, got '%s'\n", flag, s);
        exit(EX_BADFILTER);
    }
    return v;
}

/* ---- argument parsing ------------------------------------------------------ */
static const char *need_value(int argc, char **argv, int *i, const char *flag) {
    if (*i + 1 >= argc) {
        fprintf(stderr, "error: %s requires a value\n", flag);
        exit(EX_BADFILTER);
    }
    (*i)++;
    return argv[*i];
}

static void parse_filters(int argc, char **argv, int start_idx, Filters *f) {
    memset(f, 0, sizeof(*f));
    f->db_path = "/app/catalog.db";
    f->window_years = 50.0;
    for (int i = start_idx; i < argc; i++) {
        const char *a = argv[i];
        if (strcmp(a, "--db") == 0) {
            f->db_path = need_value(argc, argv, &i, a);
        } else if (strcmp(a, "--region") == 0) {
            f->region = need_value(argc, argv, &i, a);
        } else if (strcmp(a, "--lat-min") == 0) {
            f->lat_min = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_lat_min = 1;
        } else if (strcmp(a, "--lat-max") == 0) {
            f->lat_max = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_lat_max = 1;
        } else if (strcmp(a, "--lon-min") == 0) {
            f->lon_min = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_lon_min = 1;
        } else if (strcmp(a, "--lon-max") == 0) {
            f->lon_max = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_lon_max = 1;
        } else if (strcmp(a, "--start") == 0) {
            f->start = need_value(argc, argv, &i, a);
        } else if (strcmp(a, "--end") == 0) {
            f->end = need_value(argc, argv, &i, a);
        } else if (strcmp(a, "--depth-min") == 0) {
            f->depth_min = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_depth_min = 1;
        } else if (strcmp(a, "--depth-max") == 0) {
            f->depth_max = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_depth_max = 1;
        } else if (strcmp(a, "--mag-min") == 0) {
            f->mag_min = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_mag_min = 1;
        } else if (strcmp(a, "--mag-max") == 0) {
            f->mag_max = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_mag_max = 1;
        } else if (strcmp(a, "--out") == 0) {
            f->out = need_value(argc, argv, &i, a);
        } else if (strcmp(a, "--out-prefix") == 0) {
            f->out_prefix = need_value(argc, argv, &i, a);
        } else if (strcmp(a, "--targets") == 0) {
            f->targets = need_value(argc, argv, &i, a);
        } else if (strcmp(a, "--window-years") == 0) {
            f->window_years = parse_double_or_die(need_value(argc, argv, &i, a), a); f->has_window = 1;
        } else {
            fprintf(stderr, "error: unknown argument '%s'\n", a);
            exit(EX_BADFILTER);
        }
    }
    /* validation */
    if (f->has_lat_min && (f->lat_min < -90.0 || f->lat_min > 90.0)) die_usage("lat-min out of range [-90,90]");
    if (f->has_lat_max && (f->lat_max < -90.0 || f->lat_max > 90.0)) die_usage("lat-max out of range [-90,90]");
    if (f->has_lon_min && (f->lon_min < -180.0 || f->lon_min > 180.0)) die_usage("lon-min out of range [-180,180]");
    if (f->has_lon_max && (f->lon_max < -180.0 || f->lon_max > 180.0)) die_usage("lon-max out of range [-180,180]");
    if (f->has_lat_min && f->has_lat_max && f->lat_min > f->lat_max) die_usage("lat-min > lat-max");
    if (f->has_lon_min && f->has_lon_max && f->lon_min > f->lon_max) die_usage("lon-min > lon-max");
    if (f->has_depth_min && f->has_depth_max && f->depth_min > f->depth_max) die_usage("depth-min > depth-max");
    if (f->has_mag_min && f->has_mag_max && f->mag_min > f->mag_max) die_usage("mag-min > mag-max");
    if (f->start && f->end && strcmp(f->start, f->end) > 0) die_usage("start > end");
    if (f->window_years <= 0.0) die_usage("window-years must be positive");
}

/* ---- WHERE clause builder -------------------------------------------------- */
/* Appends parameterized predicates and records bind actions. We bind by walking
 * the same condition list, so order is deterministic. */
typedef struct {
    char sql[2048];
    /* deferred binds */
    int n;
    int kind[32];        /* 0=double, 1=text */
    double dval[32];
    const char *tval[32];
} Where;

static void where_build(const Filters *f, Where *w) {
    w->sql[0] = '\0';
    w->n = 0;
    strcat(w->sql, " WHERE 1=1");
    #define ADD_D(cond, v) do { strcat(w->sql, cond); w->kind[w->n]=0; w->dval[w->n]=(v); w->n++; } while (0)
    #define ADD_T(cond, v) do { strcat(w->sql, cond); w->kind[w->n]=1; w->tval[w->n]=(v); w->n++; } while (0)
    if (f->region)       ADD_T(" AND region = ?", f->region);
    if (f->has_lat_min)  ADD_D(" AND latitude >= ?", f->lat_min);
    if (f->has_lat_max)  ADD_D(" AND latitude <= ?", f->lat_max);
    if (f->has_lon_min)  ADD_D(" AND longitude >= ?", f->lon_min);
    if (f->has_lon_max)  ADD_D(" AND longitude <= ?", f->lon_max);
    if (f->start)        ADD_T(" AND time >= ?", f->start);
    if (f->end)          ADD_T(" AND time <= ?", f->end);
    if (f->has_depth_min) ADD_D(" AND depth_km >= ?", f->depth_min);
    if (f->has_depth_max) ADD_D(" AND depth_km <= ?", f->depth_max);
    if (f->has_mag_min)  ADD_D(" AND magnitude >= ?", f->mag_min);
    if (f->has_mag_max)  ADD_D(" AND magnitude <= ?", f->mag_max);
    #undef ADD_D
    #undef ADD_T
}

static void where_bind(sqlite3_stmt *st, const Where *w) {
    for (int i = 0; i < w->n; i++) {
        if (w->kind[i] == 0) sqlite3_bind_double(st, i + 1, w->dval[i]);
        else sqlite3_bind_text(st, i + 1, w->tval[i], -1, SQLITE_TRANSIENT);
    }
}

static sqlite3 *open_db(const Filters *f) {
    sqlite3 *db = NULL;
    if (sqlite3_open_v2(f->db_path, &db, SQLITE_OPEN_READONLY, NULL) != SQLITE_OK) {
        fprintf(stderr, "error: cannot open database '%s': %s\n", f->db_path, sqlite3_errmsg(db));
        exit(EX_BADFILTER);
    }
    return db;
}

/* ---- M1: query ------------------------------------------------------------- */
static int cmd_query(const Filters *f) {
    if (!f->out) die_usage("query requires --out");
    sqlite3 *db = open_db(f);
    Where w; where_build(f, &w);
    char sql[2600];
    snprintf(sql, sizeof(sql),
             "SELECT id, time, latitude, longitude, depth_km, magnitude, region FROM events%s"
             " ORDER BY time ASC, id ASC", w.sql);
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(db, sql, -1, &st, NULL) != SQLITE_OK) {
        fprintf(stderr, "error: query failed: %s\n", sqlite3_errmsg(db));
        exit(EX_BADFILTER);
    }
    where_bind(st, &w);
    FILE *out = fopen(f->out, "w");
    if (!out) { fprintf(stderr, "error: cannot write '%s'\n", f->out); exit(EX_BADFILTER); }
    fprintf(out, "id,time,latitude,longitude,depth_km,magnitude,region\n");
    while (sqlite3_step(st) == SQLITE_ROW) {
        long long id = sqlite3_column_int64(st, 0);
        const unsigned char *time = sqlite3_column_text(st, 1);
        double lat = sqlite3_column_double(st, 2);
        double lon = sqlite3_column_double(st, 3);
        double dep = sqlite3_column_double(st, 4);
        double mag = sqlite3_column_double(st, 5);
        const unsigned char *region = sqlite3_column_text(st, 6);
        fprintf(out, "%lld,%s,%.4f,%.4f,%.2f,%.1f,%s\n",
                id, time ? (const char *)time : "",
                lat, lon, dep, mag, region ? (const char *)region : "");
    }
    fclose(out);
    sqlite3_finalize(st);
    sqlite3_close(db);
    return EX_OK;
}

/* ---- statistics core ------------------------------------------------------- */
typedef struct {
    int n_total;
    int n_above_mc;
    double mc;
    double b_value;
    double b_uncertainty;
    double a_value;
    double catalog_years;
    double mag_min, mag_max;
    double gft_R;       /* best/selected fit residual percentage */
} Stats;

static int bin_index(double m) {
    return (int)floor(m / DELTA_M + 0.5);
}

/* Aki-Utsu b given a sample (mags) with cutoff mc. */
static double aki_b(const double *mags, int n, double mc, double *mean_out) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) sum += mags[i];
    double mean = sum / n;
    if (mean_out) *mean_out = mean;
    double denom = mean - (mc - DELTA_M / 2.0);
    if (denom <= 0.0) return -1.0;
    return log10(exp(1.0)) / denom;
}

/* Goodness-of-fit completeness scan over candidate Mc bins. Returns 0 on
 * success and fills *mc and *bestR; returns nonzero if no fit is possible. */
static int gft_mc(const double *mags, int n, double *mc_out, double *R_out) {
    if (n <= 0) return -1;
    int bmin = bin_index(mags[0]), bmax = bin_index(mags[0]);
    for (int i = 1; i < n; i++) {
        int b = bin_index(mags[i]);
        if (b < bmin) bmin = b;
        if (b > bmax) bmax = b;
    }
    int nbins = bmax - bmin + 1;
    if (nbins < MIN_BINS_ABOVE_MC) return -1;
    int *hist = calloc(nbins, sizeof(int));
    for (int i = 0; i < n; i++) hist[bin_index(mags[i]) - bmin]++;

    double best_R = -1e9, best_mc = 0.0;
    int found = 0; double found_mc = 0.0, found_R = 0.0;
    for (int c = 0; c < nbins - (MIN_BINS_ABOVE_MC - 1); c++) {
        double mc = (bmin + c) * DELTA_M;
        /* sample at/above this candidate */
        int ns = 0; double sum = 0.0;
        for (int i = 0; i < n; i++) {
            if (bin_index(mags[i]) >= bmin + c) { ns++; sum += mags[i]; }
        }
        if (ns < MIN_SAMPLE) continue;
        double mean = sum / ns;
        double denom = mean - (mc - DELTA_M / 2.0);
        if (denom <= 0.0) continue;
        double b = log10(exp(1.0)) / denom;
        double a = log10((double)ns) + b * mc;
        /* observed and predicted cumulative counts per bin >= candidate */
        double abs_sum = 0.0, obs_sum = 0.0;
        for (int k = c; k < nbins; k++) {
            double bin_center = (bmin + k) * DELTA_M;
            double obs_cum = 0.0;
            for (int kk = k; kk < nbins; kk++) obs_cum += hist[kk];
            double pred_cum = pow(10.0, a - b * bin_center);
            abs_sum += fabs(obs_cum - pred_cum);
            obs_sum += obs_cum;
        }
        double R = 100.0 * (1.0 - abs_sum / obs_sum);
        if (R > best_R) { best_R = R; best_mc = mc; }
        if (!found && R >= GFT_CONFIDENCE) { found = 1; found_mc = mc; found_R = R; break; }
    }
    if (found) { *mc_out = found_mc; *R_out = found_R; return 0; }
    if (best_R > -1e8) { *mc_out = best_mc; *R_out = best_R; return 0; }
    return -1;
}

/* Load filtered magnitudes (ascending) and aggregate span. */
static double *load_mags(const Filters *f, int *n_out, double *years_out,
                         double *mmin_out, double *mmax_out) {
    sqlite3 *db = open_db(f);
    Where w; where_build(f, &w);
    char agg[2700];
    snprintf(agg, sizeof(agg),
             "SELECT COUNT(*), MIN(magnitude), MAX(magnitude),"
             " (julianday(MAX(time)) - julianday(MIN(time)))/365.25 FROM events%s", w.sql);
    sqlite3_stmt *st = NULL;
    if (sqlite3_prepare_v2(db, agg, -1, &st, NULL) != SQLITE_OK) {
        fprintf(stderr, "error: %s\n", sqlite3_errmsg(db)); exit(EX_BADFILTER);
    }
    where_bind(st, &w);
    int n = 0; double years = 0.0, mmin = 0.0, mmax = 0.0;
    if (sqlite3_step(st) == SQLITE_ROW) {
        n = sqlite3_column_int(st, 0);
        mmin = sqlite3_column_double(st, 1);
        mmax = sqlite3_column_double(st, 2);
        years = sqlite3_column_double(st, 3);
    }
    sqlite3_finalize(st);
    *n_out = n; *years_out = years; *mmin_out = mmin; *mmax_out = mmax;
    if (n == 0) { sqlite3_close(db); return NULL; }
    double *mags = malloc(sizeof(double) * n);
    char q[2700];
    snprintf(q, sizeof(q),
             "SELECT magnitude FROM events%s ORDER BY magnitude ASC", w.sql);
    if (sqlite3_prepare_v2(db, q, -1, &st, NULL) != SQLITE_OK) {
        fprintf(stderr, "error: %s\n", sqlite3_errmsg(db)); exit(EX_BADFILTER);
    }
    where_bind(st, &w);
    int i = 0;
    while (sqlite3_step(st) == SQLITE_ROW && i < n) mags[i++] = sqlite3_column_double(st, 0);
    sqlite3_finalize(st);
    sqlite3_close(db);
    return mags;
}

/* Compute full statistics; exits EX_INSUFFICIENT when the sample cannot support
 * a stable estimate. */
static void compute_stats(const Filters *f, Stats *s) {
    int n; double years, mmin, mmax;
    double *mags = load_mags(f, &n, &years, &mmin, &mmax);
    if (n == 0 || mags == NULL) {
        fprintf(stderr, "error: no events match the filters\n");
        exit(EX_INSUFFICIENT);
    }
    double mc, R;
    if (gft_mc(mags, n, &mc, &R) != 0) {
        fprintf(stderr, "error: insufficient sample for completeness estimation\n");
        free(mags); exit(EX_INSUFFICIENT);
    }
    /* events at/above Mc */
    int cmin = bin_index(mc);
    int na = 0;
    for (int i = 0; i < n; i++) if (bin_index(mags[i]) >= cmin) na++;
    if (na < MIN_SAMPLE) {
        fprintf(stderr, "error: only %d events at/above Mc (need %d)\n", na, MIN_SAMPLE);
        free(mags); exit(EX_INSUFFICIENT);
    }
    double *above = malloc(sizeof(double) * na);
    int j = 0;
    for (int i = 0; i < n; i++) if (bin_index(mags[i]) >= cmin) above[j++] = mags[i];
    double mean;
    double b = aki_b(above, na, mc, &mean);
    if (b <= 0.0) {
        fprintf(stderr, "error: degenerate magnitude distribution\n");
        free(mags); free(above); exit(EX_INSUFFICIENT);
    }
    /* Shi & Bolt 1982 uncertainty */
    double var = 0.0;
    for (int i = 0; i < na; i++) var += (above[i] - mean) * (above[i] - mean);
    var = var / ((double)na * (na - 1));
    double sigma_b = 2.30 * b * b * sqrt(var);
    double a = log10((double)na) + b * mc;

    s->n_total = n;
    s->n_above_mc = na;
    s->mc = mc;
    s->b_value = b;
    s->b_uncertainty = sigma_b;
    s->a_value = a;
    s->catalog_years = years;
    s->mag_min = mmin;
    s->mag_max = mmax;
    s->gft_R = R;
    free(mags); free(above);
}

static void write_stats_json(FILE *out, const Stats *s) {
    fprintf(out, "{\n");
    fprintf(out, "  \"completeness_method\": \"goodness_of_fit\",\n");
    fprintf(out, "  \"gft_confidence\": %.1f,\n", GFT_CONFIDENCE);
    fprintf(out, "  \"delta_m\": %.1f,\n", DELTA_M);
    fprintf(out, "  \"n_total\": %d,\n", s->n_total);
    fprintf(out, "  \"n_above_mc\": %d,\n", s->n_above_mc);
    fprintf(out, "  \"mc\": %.1f,\n", s->mc);
    fprintf(out, "  \"b_value\": %.4f,\n", s->b_value);
    fprintf(out, "  \"b_uncertainty\": %.4f,\n", s->b_uncertainty);
    fprintf(out, "  \"a_value\": %.4f,\n", s->a_value);
    fprintf(out, "  \"catalog_years\": %.4f,\n", s->catalog_years);
    fprintf(out, "  \"magnitude_range\": {\"min\": %.1f, \"max\": %.1f}\n", s->mag_min, s->mag_max);
    fprintf(out, "}\n");
}

static int cmd_stats(const Filters *f) {
    Stats s; compute_stats(f, &s);
    FILE *out = f->out ? fopen(f->out, "w") : stdout;
    if (!out) { fprintf(stderr, "error: cannot write '%s'\n", f->out); exit(EX_BADFILTER); }
    write_stats_json(out, &s);
    if (f->out) fclose(out);
    return EX_OK;
}

/* ---- M3: report ------------------------------------------------------------ */
static int parse_targets(const char *spec, double *out, int max) {
    int n = 0;
    char buf[256];
    strncpy(buf, spec, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';
    char *tok = strtok(buf, ",");
    while (tok && n < max) {
        char *endp = NULL;
        double v = strtod(tok, &endp);
        if (endp == tok) die_usage("invalid --targets value");
        out[n++] = v;
        tok = strtok(NULL, ",");
    }
    return n;
}

static int cmd_report(const Filters *f) {
    if (!f->out_prefix) die_usage("report requires --out-prefix");
    Stats s; compute_stats(f, &s);

    /* reload mags for the FMD table */
    int n; double years, mmin, mmax;
    double *mags = load_mags(f, &n, &years, &mmin, &mmax);
    int bmin = bin_index(mags[0]), bmax = bin_index(mags[0]);
    for (int i = 1; i < n; i++) {
        int b = bin_index(mags[i]);
        if (b < bmin) bmin = b;
        if (b > bmax) bmax = b;
    }
    int nbins = bmax - bmin + 1;
    int *hist = calloc(nbins, sizeof(int));
    for (int i = 0; i < n; i++) hist[bin_index(mags[i]) - bmin]++;

    char path[1024];
    snprintf(path, sizeof(path), "%s_fmd.csv", f->out_prefix);
    FILE *fmd = fopen(path, "w");
    if (!fmd) { fprintf(stderr, "error: cannot write '%s'\n", path); exit(EX_BADFILTER); }
    fprintf(fmd, "magnitude,count,cumulative_count\n");
    for (int k = 0; k < nbins; k++) {
        double center = (bmin + k) * DELTA_M;
        long cum = 0;
        for (int kk = k; kk < nbins; kk++) cum += hist[kk];
        fprintf(fmd, "%.1f,%d,%ld\n", center, hist[k], cum);
    }
    fclose(fmd);

    /* exceedance */
    double targets[64];
    int nt = f->targets ? parse_targets(f->targets, targets, 64) : 3;
    if (!f->targets) { targets[0] = 5.0; targets[1] = 6.0; targets[2] = 7.0; }

    snprintf(path, sizeof(path), "%s_summary.json", f->out_prefix);
    FILE *out = fopen(path, "w");
    if (!out) { fprintf(stderr, "error: cannot write '%s'\n", path); exit(EX_BADFILTER); }
    fprintf(out, "{\n");
    fprintf(out, "  \"completeness_method\": \"goodness_of_fit\",\n");
    fprintf(out, "  \"gft_confidence\": %.1f,\n", GFT_CONFIDENCE);
    fprintf(out, "  \"delta_m\": %.1f,\n", DELTA_M);
    fprintf(out, "  \"n_total\": %d,\n", s.n_total);
    fprintf(out, "  \"n_above_mc\": %d,\n", s.n_above_mc);
    fprintf(out, "  \"mc\": %.1f,\n", s.mc);
    fprintf(out, "  \"b_value\": %.4f,\n", s.b_value);
    fprintf(out, "  \"b_uncertainty\": %.4f,\n", s.b_uncertainty);
    fprintf(out, "  \"a_value\": %.4f,\n", s.a_value);
    fprintf(out, "  \"catalog_years\": %.4f,\n", s.catalog_years);
    fprintf(out, "  \"window_years\": %.1f,\n", f->window_years);
    fprintf(out, "  \"magnitude_range\": {\"min\": %.1f, \"max\": %.1f},\n", s.mag_min, s.mag_max);
    fprintf(out, "  \"exceedance\": [\n");
    for (int t = 0; t < nt; t++) {
        double M = targets[t];
        double expected_count = pow(10.0, s.a_value - s.b_value * M);
        double annual_rate = expected_count / s.catalog_years;
        double prob = 1.0 - exp(-annual_rate * f->window_years);
        fprintf(out, "    {\"magnitude\": %.1f, \"annual_rate\": %.6f, \"exceedance_probability\": %.6f}%s\n",
                M, annual_rate, prob, (t + 1 < nt) ? "," : "");
    }
    fprintf(out, "  ]\n}\n");
    fclose(out);
    free(mags); free(hist);
    return EX_OK;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: quake <query|stats|report> [filters]\n");
        return EX_BADFILTER;
    }
    Filters f;
    parse_filters(argc, argv, 2, &f);
    if (strcmp(argv[1], "query") == 0) return cmd_query(&f);
    if (strcmp(argv[1], "stats") == 0) return cmd_stats(&f);
    if (strcmp(argv[1], "report") == 0) return cmd_report(&f);
    fprintf(stderr, "error: unknown command '%s'\n", argv[1]);
    return EX_BADFILTER;
}
QUAKE_EOF

cc -O2 -o /app/quake /app/quake.c -lsqlite3 -lm
/app/quake stats --db /app/catalog.db --region Cascadia --out /app/stats.json
echo " wrote /app/stats.json"
