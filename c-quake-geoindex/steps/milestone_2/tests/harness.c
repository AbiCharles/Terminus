/* Independent harness for milestone 2 (removal under churn).
 *
 * Builds on milestone 1: the same brute-force record, now with removal. Verifies
 * that after arbitrary insert/remove sequences the index reports the right size
 * and the right radius-query results, and that heavy churn is sanitizer-clean (no
 * use-after-free, leak-driven OOM, or out-of-bounds bucket access). Compiled with
 * the candidate's geoindex.c under UndefinedBehaviorSanitizer.
 *
 * Usage: harness <scenario>
 */
#include "geoindex.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define R 6371.0
#define D2R 0.017453292519943295769
#define MAXE 300000

typedef struct { long id; double lat, lon, mag, t; int live; } Ev;
static Ev g[MAXE];
static int gn;          /* slots ever used */
static int glive;       /* live count */

static unsigned long rng = 2463534242UL;
static double rnd(double a, double b) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return a + (b - a) * ((double)(rng >> 11) / 9007199254740992.0);
}

static double hav(double a, double o, double b, double p) {
    double p1 = a * D2R, p2 = b * D2R, dp = (b - a) * D2R, dl = (p - o) * D2R;
    double x = sin(dp / 2) * sin(dp / 2) + cos(p1) * cos(p2) * sin(dl / 2) * sin(dl / 2);
    if (x > 1) x = 1;
    return 2 * R * asin(sqrt(x));
}
static int cmpl(const void *a, const void *b) {
    long x = *(const long *)a, y = *(const long *)b; return x < y ? -1 : (x > y ? 1 : 0);
}
static size_t brute(double lat, double lon, double rad, long *bf) {
    size_t n = 0;
    for (int i = 0; i < gn; i++)
        if (g[i].live && hav(lat, lon, g[i].lat, g[i].lon) <= rad) bf[n++] = g[i].id;
    qsort(bf, n, sizeof(long), cmpl);
    return n;
}
static void add(long id, double lat, double lon, double mag, double t) {
    if (gi_insert(id, lat, lon, mag, t) != 0) { printf("FAIL insert nonzero\n"); exit(1); }
    g[gn].id = id; g[gn].lat = lat; g[gn].lon = lon; g[gn].mag = mag; g[gn].t = t; g[gn].live = 1; gn++; glive++;
}
/* remove the live record at slot s (by id) from both the index and our mirror */
static int del_slot(int s) {
    if (!g[s].live) return 0;
    int rc = gi_remove(g[s].id);
    if (rc != 0) { printf("FAIL remove of live id %ld returned %d\n", g[s].id, rc); exit(1); }
    g[s].live = 0; glive--;
    return 1;
}
static int check_query(double lat, double lon, double rad) {
    static long out[MAXE], bf[MAXE];
    size_t got = gi_query_radius(lat, lon, rad, out, MAXE);
    size_t exp = brute(lat, lon, rad, bf);
    if (got != exp) { printf("FAIL count got=%zu exp=%zu\n", got, exp); return 0; }
    for (size_t i = 0; i < exp; i++) if (out[i] != bf[i]) { printf("FAIL id mismatch\n"); return 0; }
    return 1;
}

static int sc_remove_basic(void) {
    for (int i = 0; i < 4000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
    for (int i = 0; i < 1500; i++) { int s = (int)rnd(0, gn); del_slot(s); }
    if (gi_size() != (size_t)glive) { printf("FAIL size %zu vs %d\n", gi_size(), glive); return 1; }
    for (int q = 0; q < 200; q++) if (!check_query(rnd(-80, 80), rnd(-179, 179), rnd(40, 900))) return 1;
    return 0;
}

static int sc_remove_nonexistent(void) {
    for (int i = 0; i < 1000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
    if (gi_remove(999999) == 0) { printf("FAIL remove of absent id succeeded\n"); return 1; }
    del_slot(10);
    if (gi_remove(g[10].id) == 0) { printf("FAIL double-remove succeeded\n"); return 1; }
    if (gi_size() != (size_t)glive) { printf("FAIL size after\n"); return 1; }
    return 0;
}

static int sc_remove_all(void) {
    for (int i = 0; i < 3000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
    for (int s = 0; s < gn; s++) del_slot(s);
    if (gi_size() != 0) { printf("FAIL size after remove-all %zu\n", gi_size()); return 1; }
    long out[8];
    if (gi_query_radius(0, 0, 5000, out, 8) != 0) { printf("FAIL query after remove-all\n"); return 1; }
    return 0;
}

/* heavy interleaved insert/remove/reinsert with overlapping ids reused, then
 * query checks throughout — stresses bucket maintenance and slot reuse for UB. */
static int sc_churn(void) {
    long nextid = 0;
    for (int round = 0; round < 30; round++) {
        for (int i = 0; i < 2000; i++) add(nextid++, rnd(-85, 85), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
        for (int i = 0; i < 1500; i++) { int s = (int)rnd(0, gn); del_slot(s); }
        if (round % 5 == 0)
            for (int q = 0; q < 40; q++) if (!check_query(rnd(-85, 85), rnd(-179, 179), rnd(40, 900))) return 1;
    }
    if (gi_size() != (size_t)glive) { printf("FAIL churn size\n"); return 1; }
    for (int q = 0; q < 200; q++) if (!check_query(rnd(-85, 85), rnd(-179, 179), rnd(40, 900))) return 1;
    return 0;
}

/* large-scale churn: a flat scan still cannot keep up with the query volume. */
static int sc_scale_churn(void) {
    for (int i = 0; i < 200000; i++) add(i, rnd(-85, 85), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
    for (int i = 0; i < 80000; i++) { int s = (int)rnd(0, gn); del_slot(s); }
    for (int i = 200000; i < 260000; i++) add(i, rnd(-85, 85), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
    if (gi_size() != (size_t)glive) { printf("FAIL scale_churn size\n"); return 1; }
    for (int q = 0; q < 20000; q++) {
        double lat = rnd(-85, 85), lon = rnd(-179, 179), rad = rnd(20, 400);
        static long out[MAXE];
        size_t got = gi_query_radius(lat, lon, rad, out, MAXE);
        if (q % 1000 == 0) {
            static long bf[MAXE];
            size_t exp = brute(lat, lon, rad, bf);
            if (got != exp) { printf("FAIL scale_churn count got=%zu exp=%zu\n", got, exp); return 1; }
            for (size_t i = 0; i < exp; i++) if (out[i] != bf[i]) { printf("FAIL scale_churn id\n"); return 1; }
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { printf("usage: harness <scenario>\n"); return 2; }
    gi_reset(); gn = 0; glive = 0;
    const char *s = argv[1];
    int rc;
    if (!strcmp(s, "remove_basic")) rc = sc_remove_basic();
    else if (!strcmp(s, "remove_nonexistent")) rc = sc_remove_nonexistent();
    else if (!strcmp(s, "remove_all")) rc = sc_remove_all();
    else if (!strcmp(s, "churn")) rc = sc_churn();
    else if (!strcmp(s, "scale_churn")) rc = sc_scale_churn();
    else { printf("unknown scenario %s\n", s); return 2; }
    if (rc == 0) printf("OK\n");
    return rc;
}
