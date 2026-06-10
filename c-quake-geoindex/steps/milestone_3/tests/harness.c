/* Independent harness for milestone 3 (Gardner-Knopoff declustering).
 *
 * Builds the index, then checks gi_decluster against an independent brute-force
 * Gardner-Knopoff implementation kept entirely inside the harness. Compiled with
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
#define MAXE 30000

typedef struct { long id; double lat, lon, mag, t; int live; } Ev;
static Ev g[MAXE];
static int gn;

static unsigned long rng = 0x9e3779b97f4a7c15UL;
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
static void add(long id, double lat, double lon, double mag, double t) {
    if (gi_insert(id, lat, lon, mag, t) != 0) { printf("FAIL insert nonzero\n"); exit(1); }
    g[gn].id = id; g[gn].lat = lat; g[gn].lon = lon; g[gn].mag = mag; g[gn].t = t; g[gn].live = 1; gn++;
}

/* brute-force GK over the live mirror; fill surv (ascending), return count */
static int *gk_recs_order;  /* indices into a compact live array */
static Ev *gk_live;
static int gk_cmp(const void *a, const void *b) {
    const Ev *x = &gk_live[*(const int *)a], *y = &gk_live[*(const int *)b];
    if (x->mag != y->mag) return x->mag > y->mag ? -1 : 1;
    if (x->t != y->t) return x->t < y->t ? -1 : 1;
    return x->id < y->id ? -1 : (x->id > y->id ? 1 : 0);
}
static size_t brute_decluster(long *surv) {
    static Ev live[MAXE];
    int n = 0;
    for (int i = 0; i < gn; i++) if (g[i].live) live[n++] = g[i];
    static int order[MAXE], removed[MAXE];
    for (int i = 0; i < n; i++) { order[i] = i; removed[i] = 0; }
    gk_live = live; (void)gk_recs_order;
    qsort(order, n, sizeof(int), gk_cmp);
    for (int oi = 0; oi < n; oi++) {
        int i = order[oi];
        if (removed[i]) continue;
        double M = live[i].mag;
        double L = pow(10, 0.1238 * M + 0.983);
        double T = (M >= 6.5) ? pow(10, 0.5409 * M - 0.547) : pow(10, 0.032 * M + 2.7389);
        for (int k = 0; k < n; k++) {
            if (k == i || removed[k]) continue;
            double dt = live[k].t - live[i].t; if (dt < 0) dt = -dt;
            if (dt <= T && hav(live[i].lat, live[i].lon, live[k].lat, live[k].lon) <= L) removed[k] = 1;
        }
    }
    size_t ns = 0;
    for (int i = 0; i < n; i++) if (!removed[i]) surv[ns++] = live[i].id;
    qsort(surv, ns, sizeof(long), cmpl);
    return ns;
}

static int check_decluster(void) {
    static long out[MAXE], bf[MAXE];
    size_t got = gi_decluster(out, MAXE);
    size_t exp = brute_decluster(bf);
    if (got != exp) { printf("FAIL decluster count got=%zu exp=%zu\n", got, exp); return 0; }
    for (size_t i = 0; i < exp; i++) if (out[i] != bf[i]) { printf("FAIL decluster id[%zu]=%ld exp=%ld\n", i, out[i], bf[i]); return 0; }
    return 1;
}

static int sc_random(void) {
    for (int i = 0; i < 5000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7.5), rnd(0, 7300));
    return check_decluster() ? 0 : 1;
}

/* mainshocks each surrounded by a compact aftershock cluster — declustering must
 * keep the mainshocks and drop the aftershocks */
static int sc_clustered(void) {
    long id = 0;
    int nmain = 60;
    long mainids[64];
    for (int m = 0; m < nmain; m++) {
        double la = rnd(-70, 70), lo = rnd(-170, 170), M = rnd(5.5, 7.2), t0 = rnd(500, 6800);
        mainids[m] = id;
        add(id++, la, lo, M, t0);
        double L = pow(10, 0.1238 * M + 0.983);
        int naft = 80;
        for (int a = 0; a < naft; a++) {
            double rkm = 0.3 * L * sqrt(rnd(0, 1)), ang = rnd(0, 6.283185);
            double alat = la + (rkm * cos(ang)) / 111.0;
            double alon = lo + (rkm * sin(ang)) / (111.0 * cos(la * D2R));
            if (alat > 89) alat = 89; if (alat < -89) alat = -89;
            if (alon > 179.9) alon = 179.9; if (alon < -179.9) alon = -179.9;
            add(id++, alat, alon, rnd(0.5, M - 0.5), t0 + rnd(0, 200));
        }
    }
    static long out[MAXE], bf[MAXE];
    size_t got = gi_decluster(out, MAXE);
    size_t exp = brute_decluster(bf);
    if (got != exp) { printf("FAIL clustered count got=%zu exp=%zu\n", got, exp); return 1; }
    for (size_t i = 0; i < exp; i++) if (out[i] != bf[i]) { printf("FAIL clustered id\n"); return 1; }
    /* every mainshock must survive (it is the largest in its cluster) */
    for (int m = 0; m < nmain; m++) {
        int found = 0;
        for (size_t i = 0; i < got; i++) if (out[i] == mainids[m]) { found = 1; break; }
        if (!found) { printf("FAIL mainshock %ld removed\n", mainids[m]); return 1; }
    }
    return 0;
}

static int sc_after_remove(void) {
    for (int i = 0; i < 6000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7.5), rnd(0, 7300));
    for (int i = 0; i < 2500; i++) {
        int s = (int)rnd(0, gn);
        if (g[s].live) { if (gi_remove(g[s].id) != 0) { printf("FAIL remove\n"); return 1; } g[s].live = 0; }
    }
    return check_decluster() ? 0 : 1;
}

static int sc_unchanged(void) {
    for (int i = 0; i < 4000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7.5), rnd(0, 7300));
    size_t before = gi_size();
    static long out[MAXE];
    gi_decluster(out, MAXE);
    if (gi_size() != before) { printf("FAIL decluster mutated size %zu->%zu\n", before, gi_size()); return 1; }
    /* a query must still see all events (decluster is non-destructive) */
    if (!check_decluster()) return 1;  /* and a second decluster gives the same answer */
    return 0;
}

static int sc_capacity(void) {
    for (int i = 0; i < 4000; i++) add(i, rnd(-80, 80), rnd(-179, 179), rnd(0.5, 7.5), rnd(0, 7300));
    static long bf[MAXE];
    size_t exp = brute_decluster(bf);
    long small[25];
    size_t got = gi_decluster(small, 25);
    if (got != exp) { printf("FAIL capacity total got=%zu exp=%zu\n", got, exp); return 1; }
    for (int i = 0; i < 25; i++) if (small[i] != bf[i]) { printf("FAIL capacity smallest[%d]\n", i); return 1; }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { printf("usage: harness <scenario>\n"); return 2; }
    gi_reset(); gn = 0;
    const char *s = argv[1];
    int rc;
    if (!strcmp(s, "random")) rc = sc_random();
    else if (!strcmp(s, "clustered")) rc = sc_clustered();
    else if (!strcmp(s, "after_remove")) rc = sc_after_remove();
    else if (!strcmp(s, "unchanged")) rc = sc_unchanged();
    else if (!strcmp(s, "capacity")) rc = sc_capacity();
    else { printf("unknown scenario %s\n", s); return 2; }
    if (rc == 0) printf("OK\n");
    return rc;
}
