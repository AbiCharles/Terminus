/* Independent harness for milestone 1 (insert + radius query).
 *
 * Compiled together with the candidate's geoindex.c under
 * UndefinedBehaviorSanitizer. The harness keeps its OWN record of every inserted
 * event and verifies gi_query_radius against a brute-force haversine scan, so it
 * trusts none of the index's internal bookkeeping. Each scenario prints "OK" and
 * exits 0 on success; a wrong answer or a sanitizer abort yields a non-zero exit.
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

typedef struct { long id; double lat, lon, mag, t; } Ev;
static Ev g[MAXE];
static int gn;

static unsigned long rng = 88172645463325252UL;
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
    long x = *(const long *)a, y = *(const long *)b;
    return x < y ? -1 : (x > y ? 1 : 0);
}

static size_t brute(double lat, double lon, double rad, long *bf) {
    size_t n = 0;
    for (int i = 0; i < gn; i++)
        if (hav(lat, lon, g[i].lat, g[i].lon) <= rad) bf[n++] = g[i].id;
    qsort(bf, n, sizeof(long), cmpl);
    return n;
}

static void add(long id, double lat, double lon, double mag, double t) {
    if (gi_insert(id, lat, lon, mag, t) != 0) { printf("FAIL insert returned nonzero\n"); exit(1); }
    g[gn].id = id; g[gn].lat = lat; g[gn].lon = lon; g[gn].mag = mag; g[gn].t = t; gn++;
}

static int check_query(double lat, double lon, double rad) {
    static long out[MAXE], bf[MAXE];
    size_t got = gi_query_radius(lat, lon, rad, out, MAXE);
    size_t exp = brute(lat, lon, rad, bf);
    if (got != exp) { printf("FAIL count got=%zu exp=%zu at (%.3f,%.3f,r=%.1f)\n", got, exp, lat, lon, rad); return 0; }
    for (size_t i = 0; i < exp; i++)
        if (out[i] != bf[i]) { printf("FAIL id[%zu]=%ld exp=%ld\n", i, out[i], bf[i]); return 0; }
    return 1;
}

static int sc_basic(void) {
    for (int i = 0; i < 3000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
    if (gi_size() != 3000) { printf("FAIL size=%zu\n", gi_size()); return 1; }
    for (int q = 0; q < 200; q++)
        if (!check_query(rnd(-80, 80), rnd(-179, 179), rnd(30, 900))) return 1;
    return 0;
}

static int sc_wrap(void) {
    long id = 0;
    for (int i = 0; i < 4000; i++) {
        double lon = (i % 2) ? rnd(176, 180) : rnd(-180, -176);
        add(id++, rnd(-85, 85), lon, rnd(0.5, 7), rnd(0, 7300));
    }
    for (int i = 0; i < 1000; i++) add(id++, rnd(70, 89), rnd(-179, 179), rnd(0.5, 7), rnd(0, 7300));
    double lons[] = {179.5, -179.5, 180.0, -180.0, 178.0};
    for (int q = 0; q < 5; q++)
        for (int r = 0; r < 40; r++)
            if (!check_query(rnd(-85, 85), lons[q], rnd(50, 700))) return 1;
    for (int q = 0; q < 60; q++)
        if (!check_query(rnd(75, 89), rnd(-179, 179), rnd(50, 1500))) return 1;
    return 0;
}

static int sc_capacity(void) {
    for (int i = 0; i < 5000; i++) add(i, rnd(10, 12), rnd(10, 12), rnd(0.5, 7), rnd(0, 7300));
    static long bf[MAXE];
    size_t exp = brute(11, 11, 400, bf);
    if (exp < 50) { printf("FAIL cluster not dense enough exp=%zu\n", exp); return 1; }
    long small[20];
    size_t got = gi_query_radius(11, 11, 400, small, 20);
    if (got != exp) { printf("FAIL capacity total got=%zu exp=%zu\n", got, exp); return 1; }
    for (int i = 0; i < 20; i++)
        if (small[i] != bf[i]) { printf("FAIL capacity smallest-id[%d]\n", i); return 1; }
    return 0;
}

static int sc_empty(void) {
    long out[8];
    if (gi_query_radius(0, 0, 100, out, 8) != 0) { printf("FAIL nonempty on empty\n"); return 1; }
    if (gi_size() != 0) { printf("FAIL size nonzero on empty\n"); return 1; }
    return 0;
}

static int sc_scale(void) {
    for (int i = 0; i < 250000; i++) add(i, rnd(-85, 85), rnd(-179, 179), rnd(0.5, 7.5), rnd(0, 7300));
    if (gi_size() != 250000) { printf("FAIL scale size=%zu\n", gi_size()); return 1; }
    for (int q = 0; q < 30000; q++) {
        double lat = rnd(-85, 85), lon = rnd(-179, 179), rad = rnd(20, 400);
        static long out[MAXE];
        size_t got = gi_query_radius(lat, lon, rad, out, MAXE);
        if (q % 500 == 0) {
            static long bf[MAXE];
            size_t exp = brute(lat, lon, rad, bf);
            if (got != exp) { printf("FAIL scale count got=%zu exp=%zu\n", got, exp); return 1; }
            for (size_t i = 0; i < exp; i++) if (out[i] != bf[i]) { printf("FAIL scale id\n"); return 1; }
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { printf("usage: harness <scenario>\n"); return 2; }
    gi_reset(); gn = 0;
    const char *s = argv[1];
    int rc;
    if (!strcmp(s, "basic")) rc = sc_basic();
    else if (!strcmp(s, "wrap")) rc = sc_wrap();
    else if (!strcmp(s, "capacity")) rc = sc_capacity();
    else if (!strcmp(s, "empty")) rc = sc_empty();
    else if (!strcmp(s, "scale")) rc = sc_scale();
    else { printf("unknown scenario %s\n", s); return 2; }
    if (rc == 0) printf("OK\n");
    return rc;
}
