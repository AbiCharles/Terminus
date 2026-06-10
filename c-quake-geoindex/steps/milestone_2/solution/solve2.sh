#!/usr/bin/env bash
set -euo pipefail

# Milestone 2 oracle: write the complete spatial-index implementation to
# /app/geoindex.c (it satisfies all milestones; the verifier compiles it with the
# milestone's harness under UBSan). Self-contained across milestones.
cat > /app/geoindex.c <<'GEOINDEX_EOF'
/* Reference geoindex: a 1-degree spatial grid over a stable event slot array,
 * with an id->slot hash map. Radius queries scan only the candidate cells a
 * latitude-aware degree window can reach, then exact-filter by haversine. */
#include "geoindex.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

#define CELL_DEG 1.0
#define NLAT 180
#define NLON 360
#define NCELL (NLAT * NLON)
#define DEG2RAD 0.017453292519943295769
#define KM_PER_DEG_LAT 110.574
#define KM_PER_DEG_LON 111.320

typedef struct { long id; double lat, lon, mag, t; int live; } Event;

static Event *g_ev = NULL;
static size_t g_cap = 0, g_live = 0;
static int *g_free = NULL;
static size_t g_nfree = 0, g_fcap = 0;

typedef struct { int *slot; size_t n, cap; } Cell;
static Cell *g_grid = NULL;

static long *g_key = NULL;
static int *g_val = NULL;
static size_t g_mcap = 0, g_mcnt = 0;

static int latbin(double lat) { int b = (int)floor((lat + 90.0) / CELL_DEG); return b < 0 ? 0 : (b >= NLAT ? NLAT - 1 : b); }
static int lonbin(double lon) { int b = (int)floor((lon + 180.0) / CELL_DEG); return b < 0 ? 0 : (b >= NLON ? NLON - 1 : b); }

static double haversine(double la1, double lo1, double la2, double lo2) {
    double p1 = la1 * DEG2RAD, p2 = la2 * DEG2RAD;
    double dp = (la2 - la1) * DEG2RAD, dl = (lo2 - lo1) * DEG2RAD;
    double a = sin(dp / 2) * sin(dp / 2) + cos(p1) * cos(p2) * sin(dl / 2) * sin(dl / 2);
    if (a > 1.0) a = 1.0;
    return 2.0 * GI_EARTH_RADIUS_KM * asin(sqrt(a));
}

static void map_grow(void) {
    size_t nc = g_mcap ? g_mcap * 2 : 1024;
    long *nk = malloc(nc * sizeof(long));
    int *nv = malloc(nc * sizeof(int));
    for (size_t i = 0; i < nc; i++) nk[i] = -1;
    for (size_t i = 0; i < g_mcap; i++) {
        if (g_key[i] < 0) continue;
        size_t h = (size_t)((unsigned long)g_key[i] * 1099511628211UL) & (nc - 1);
        while (nk[h] != -1) h = (h + 1) & (nc - 1);
        nk[h] = g_key[i]; nv[h] = g_val[i];
    }
    free(g_key); free(g_val);
    g_key = nk; g_val = nv; g_mcap = nc;
}
static void map_put(long id, int slot) {
    if ((g_mcnt + 1) * 2 >= g_mcap) map_grow();
    size_t h = (size_t)((unsigned long)id * 1099511628211UL) & (g_mcap - 1);
    while (g_key[h] >= 0 && g_key[h] != id) h = (h + 1) & (g_mcap - 1);
    if (g_key[h] != id) g_mcnt++;
    g_key[h] = id; g_val[h] = slot;
}
static int map_get(long id) {
    if (!g_mcap) return -1;
    size_t h = (size_t)((unsigned long)id * 1099511628211UL) & (g_mcap - 1);
    while (g_key[h] != -1) { if (g_key[h] == id) return g_val[h]; h = (h + 1) & (g_mcap - 1); }
    return -1;
}
static void map_del(long id) {
    if (!g_mcap) return;
    size_t h = (size_t)((unsigned long)id * 1099511628211UL) & (g_mcap - 1);
    while (g_key[h] != -1) {
        if (g_key[h] == id) { g_key[h] = -2; g_mcnt--; return; }
        h = (h + 1) & (g_mcap - 1);
    }
}

static void cell_push(int cell, int slot) {
    Cell *c = &g_grid[cell];
    if (c->n == c->cap) { c->cap = c->cap ? c->cap * 2 : 4; c->slot = realloc(c->slot, c->cap * sizeof(int)); }
    c->slot[c->n++] = slot;
}
static void cell_remove(int cell, int slot) {
    Cell *c = &g_grid[cell];
    for (size_t i = 0; i < c->n; i++) if (c->slot[i] == slot) { c->slot[i] = c->slot[--c->n]; return; }
}

int gi_insert(long id, double lat, double lon, double mag, double t) {
    if (!g_grid) g_grid = calloc(NCELL, sizeof(Cell));
    int slot;
    if (g_nfree > 0) slot = g_free[--g_nfree];
    else {
        if (g_live == g_cap) { g_cap = g_cap ? g_cap * 2 : 1024; g_ev = realloc(g_ev, g_cap * sizeof(Event)); }
        slot = (int)g_live;
    }
    g_ev[slot].id = id; g_ev[slot].lat = lat; g_ev[slot].lon = lon;
    g_ev[slot].mag = mag; g_ev[slot].t = t; g_ev[slot].live = 1;
    cell_push(latbin(lat) * NLON + lonbin(lon), slot);
    map_put(id, slot);
    g_live++;
    return 0;
}

size_t gi_size(void) { return g_live; }

int gi_remove(long id) {
    int slot = map_get(id);
    if (slot < 0 || !g_ev[slot].live) return 1;
    cell_remove(latbin(g_ev[slot].lat) * NLON + lonbin(g_ev[slot].lon), slot);
    g_ev[slot].live = 0;
    map_del(id);
    if (g_nfree == g_fcap) { g_fcap = g_fcap ? g_fcap * 2 : 1024; g_free = realloc(g_free, g_fcap * sizeof(int)); }
    g_free[g_nfree++] = slot;
    g_live--;
    return 0;
}

static int cmp_long(const void *a, const void *b) {
    long x = *(const long *)a, y = *(const long *)b;
    return x < y ? -1 : (x > y ? 1 : 0);
}

size_t gi_query_radius(double lat, double lon, double radius_km, long *out_ids, size_t max) {
    if (!g_grid) return 0;
    double dlat = radius_km / KM_PER_DEG_LAT + CELL_DEG;          /* +1 cell margin */
    double worst = fabs(lat) + dlat; if (worst > 89.9) worst = 89.9;
    double cl = cos(worst * DEG2RAD); if (cl < 1e-9) cl = 1e-9;   /* smallest km/deg-lon in band */
    double dlon = radius_km / (KM_PER_DEG_LON * cl) + CELL_DEG;   /* +1 cell margin */
    int lo_la = latbin(lat - dlat), hi_la = latbin(lat + dlat);
    int lo_lo, hi_lo;
    if (dlon >= 180.0) { lo_lo = 0; hi_lo = NLON - 1; }
    else {
        lo_lo = (int)floor((lon - dlon + 180.0) / CELL_DEG);
        hi_lo = (int)floor((lon + dlon + 180.0) / CELL_DEG);
        if (hi_lo - lo_lo + 1 >= NLON) { lo_lo = 0; hi_lo = NLON - 1; }
    }
    long *hits = NULL; size_t nh = 0, hc = 0;
    for (int la = lo_la; la <= hi_la; la++) {
        for (int b = lo_lo; b <= hi_lo; b++) {
            int loi = ((b % NLON) + NLON) % NLON;
            Cell *c = &g_grid[la * NLON + loi];
            for (size_t k = 0; k < c->n; k++) {
                Event *e = &g_ev[c->slot[k]];
                if (haversine(lat, lon, e->lat, e->lon) <= radius_km) {
                    if (nh == hc) { hc = hc ? hc * 2 : 64; hits = realloc(hits, hc * sizeof(long)); }
                    hits[nh++] = e->id;
                }
            }
        }
    }
    if (nh) qsort(hits, nh, sizeof(long), cmp_long);
    for (size_t i = 0; i < nh && i < max; i++) out_ids[i] = hits[i];
    free(hits);
    return nh;
}

typedef struct { long id; double lat, lon, mag, t; } Rec;
static Rec *g_sort_recs;
static int gk_cmp_idx(const void *a, const void *b) {
    const Rec *x = &g_sort_recs[*(const int *)a], *y = &g_sort_recs[*(const int *)b];
    if (x->mag != y->mag) return x->mag > y->mag ? -1 : 1;
    if (x->t != y->t) return x->t < y->t ? -1 : 1;
    return x->id < y->id ? -1 : (x->id > y->id ? 1 : 0);
}
static double gk_L(double m) { return pow(10.0, 0.1238 * m + 0.983); }
static double gk_T(double m) { return m >= 6.5 ? pow(10.0, 0.5409 * m - 0.547) : pow(10.0, 0.032 * m + 2.7389); }

size_t gi_decluster(long *out_ids, size_t max) {
    size_t n = g_live;
    if (n == 0) return 0;
    Rec *r = malloc(n * sizeof(Rec));
    size_t j = 0;
    for (size_t s = 0; s < g_cap; s++) if (g_ev[s].live) {
        r[j].id = g_ev[s].id; r[j].lat = g_ev[s].lat; r[j].lon = g_ev[s].lon;
        r[j].mag = g_ev[s].mag; r[j].t = g_ev[s].t; j++;
    }
    int *removed = calloc(n, sizeof(int));
    int *porder = malloc(n * sizeof(int));
    for (size_t i = 0; i < n; i++) porder[i] = (int)i;
    g_sort_recs = r;
    qsort(porder, n, sizeof(int), gk_cmp_idx);
    for (size_t oi = 0; oi < n; oi++) {
        int i = porder[oi];
        if (removed[i]) continue;
        double L = gk_L(r[i].mag), T = gk_T(r[i].mag);
        for (size_t k = 0; k < n; k++) {
            if ((int)k == i || removed[k]) continue;
            double dt = r[k].t - r[i].t; if (dt < 0) dt = -dt;
            if (dt <= T && haversine(r[i].lat, r[i].lon, r[k].lat, r[k].lon) <= L) removed[k] = 1;
        }
    }
    long *surv = malloc(n * sizeof(long));
    size_t ns = 0;
    for (size_t i = 0; i < n; i++) if (!removed[i]) surv[ns++] = r[i].id;
    qsort(surv, ns, sizeof(long), cmp_long);
    for (size_t i = 0; i < ns && i < max; i++) out_ids[i] = surv[i];
    free(r); free(removed); free(porder); free(surv);
    return ns;
}

void gi_reset(void) {
    if (g_grid) { for (int i = 0; i < NCELL; i++) free(g_grid[i].slot); free(g_grid); g_grid = NULL; }
    free(g_ev); g_ev = NULL; g_cap = 0; g_live = 0;
    free(g_free); g_free = NULL; g_nfree = 0; g_fcap = 0;
    free(g_key); g_key = NULL; free(g_val); g_val = NULL; g_mcap = 0; g_mcnt = 0;
}
GEOINDEX_EOF

# sanity compile-check (the verifier recompiles with its harness)
gcc -std=c11 -O2 -fsanitize=undefined -I/app -c /app/geoindex.c -o /tmp/geoindex.o
echo " wrote and compiled /app/geoindex.c (milestone 2)"
