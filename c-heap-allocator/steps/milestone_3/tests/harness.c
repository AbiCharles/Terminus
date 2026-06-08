/*
 * Independent verification harness for the fixed-arena allocator.
 *
 * It is compiled together with the candidate's allocator.c under
 * UndefinedBehaviorSanitizer and run once per scenario
 * (argv[1]). Each scenario exercises the allocator and checks the invariants
 * itself — it never trusts the allocator's own bookkeeping. On success it
 * prints "OK" and exits 0; on any violation it prints "FAIL: <reason>" and
 * exits non-zero. A sanitizer abort also yields a non-zero exit.
 *
 * The harness keeps its own record of every live allocation (pointer, payload
 * size, and a content fingerprint) so it can independently detect overlapping
 * regions, misalignment, and silent corruption.
 */
#include "allocator.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MAXLIVE 20000

static void *g_p[MAXLIVE];
static size_t g_sz[MAXLIVE];
static unsigned char g_seed[MAXLIVE];
static int g_n = 0;

static int fail(const char *msg) {
    printf("FAIL: %s\n", msg);
    return 1;
}

static void pat_fill(void *p, size_t sz, unsigned char seed) {
    unsigned char *q = (unsigned char *)p;
    for (size_t i = 0; i < sz; i++) q[i] = (unsigned char)(seed ^ (unsigned)(i * 31u));
}

static int pat_check(void *p, size_t sz, unsigned char seed) {
    unsigned char *q = (unsigned char *)p;
    for (size_t i = 0; i < sz; i++)
        if (q[i] != (unsigned char)(seed ^ (unsigned)(i * 31u))) return 0;
    return 1;
}

/* Record a fresh allocation, checking alignment and non-overlap against every
 * other live block, then stamp it with its fingerprint. Returns 1 on failure. */
static int track(void *p, size_t sz, unsigned char seed) {
    if (p == NULL) return fail("unexpected NULL from allocator");
    if (((uintptr_t)p % ALLOC_ALIGNMENT) != 0) return fail("pointer is not 16-byte aligned");
    unsigned char *a = (unsigned char *)p;
    for (int i = 0; i < g_n; i++) {
        unsigned char *b = (unsigned char *)g_p[i];
        if (a < b + g_sz[i] && b < a + sz) return fail("allocation overlaps a live block");
    }
    if (g_n >= MAXLIVE) return fail("harness live table overflow");
    g_p[g_n] = p;
    g_sz[g_n] = sz;
    g_seed[g_n] = seed;
    pat_fill(p, sz, seed);
    g_n++;
    return 0;
}

static void untrack(int i) {
    g_p[i] = g_p[g_n - 1];
    g_sz[i] = g_sz[g_n - 1];
    g_seed[i] = g_seed[g_n - 1];
    g_n--;
}

static int verify_all(void) {
    for (int i = 0; i < g_n; i++)
        if (!pat_check(g_p[i], g_sz[i], g_seed[i])) return fail("live block contents were corrupted");
    return 0;
}

/* Deterministic PRNG so the workload is identical on every platform/run. */
static unsigned long g_rng = 0x9e3779b9UL;
static unsigned rnd(void) {
    g_rng = g_rng * 1103515245UL + 12345UL;
    return (unsigned)((g_rng >> 16) & 0x7fffffffUL);
}

/* ---- milestone 1: arena, alignment, bounds, no corruption ---- */

static int sc_align(void) {
    const size_t sizes[] = {1, 8, 15, 16, 17, 31, 64, 100, 255, 256, 500};
    for (int r = 0; r < 16; r++)
        for (size_t k = 0; k < sizeof(sizes) / sizeof(sizes[0]); k++)
            if (track(xmalloc(sizes[k]), sizes[k], (unsigned char)(r * 7 + k))) return 1;
    return verify_all();
}

static int sc_integrity(void) {
    for (int i = 0; i < 200; i++)
        if (track(xmalloc((size_t)(64 + i)), (size_t)(64 + i), (unsigned char)(i * 5))) return 1;
    if (verify_all()) return 1;
    int w = 0;
    for (int i = 0; i < g_n; i++) {
        if (i & 1) {
            xfree(g_p[i]);
        } else {
            g_p[w] = g_p[i];
            g_sz[w] = g_sz[i];
            g_seed[w] = g_seed[i];
            w++;
        }
    }
    g_n = w;
    if (verify_all()) return 1;
    for (int i = 0; i < 50; i++)
        if (track(xmalloc(128), 128, (unsigned char)(200 + i))) return 1;
    return verify_all();
}

static int sc_oom(void) {
    int got_null = 0;
    for (int i = 0; i < 100000; i++) {
        void *p = xmalloc(4096);
        if (p == NULL) {
            got_null = 1;
            break;
        }
        if (track(p, 4096, (unsigned char)i)) return 1;
    }
    if (!got_null) return fail("arena never reported exhaustion under unrelenting pressure");
    return verify_all();
}

static int sc_zero_null(void) {
    if (xmalloc(0) != NULL) return fail("xmalloc(0) must return NULL");
    xfree(NULL); /* must not crash */
    void *p = xmalloc(32);
    if (track(p, 32, 1)) return 1;
    xfree(p);
    untrack(0);
    return 0;
}

/* ---- milestone 2: reuse, splitting, calloc ---- */

static int sc_reuse(void) {
    for (int i = 0; i < 20000; i++) {
        unsigned char *p = (unsigned char *)xmalloc(256);
        if (p == NULL) return fail("freed memory is not reused (exhausted during churn)");
        if (((uintptr_t)p % ALLOC_ALIGNMENT) != 0) return fail("pointer is not 16-byte aligned");
        memset(p, (i & 0xff), 256);
        for (int j = 0; j < 256; j++)
            if (p[j] != (unsigned char)(i & 0xff)) return fail("written bytes did not survive");
        xfree(p);
    }
    return 0;
}

static int sc_split(void) {
    void *big = xmalloc(8192);
    if (big == NULL) return fail("could not allocate 8192 bytes");
    xfree(big);
    void *a = xmalloc(1024);
    void *b = xmalloc(1024);
    if (a == NULL || b == NULL) return fail("two sub-allocations from one free region failed (no split)");
    if (track(a, 1024, 1)) return 1;
    if (track(b, 1024, 2)) return 1;
    return verify_all();
}

static int sc_calloc_zero(void) {
    unsigned char *p = (unsigned char *)xcalloc(100, 8);
    if (p == NULL) return fail("xcalloc(100, 8) returned NULL");
    if (((uintptr_t)p % ALLOC_ALIGNMENT) != 0) return fail("xcalloc pointer is not 16-byte aligned");
    for (int i = 0; i < 800; i++)
        if (p[i] != 0) return fail("xcalloc memory was not zeroed");
    /* xcalloc must honour the same alignment + non-overlap guarantees as xmalloc:
     * track it alongside other live allocations (overwrites the zeroed content). */
    if (track((void *)p, 800, 42)) return 1;
    void *q = xmalloc(64);
    if (track(q, 64, 43)) return 1;
    unsigned char *r = (unsigned char *)xcalloc(10, 4);
    if (r == NULL) return fail("xcalloc(10, 4) returned NULL");
    for (int i = 0; i < 40; i++)
        if (r[i] != 0) return fail("second xcalloc block was not zeroed");
    if (track((void *)r, 40, 44)) return 1;
    return verify_all();
}

static int sc_calloc_overflow(void) {
    if (xcalloc((size_t)-1, 2) != NULL) return fail("xcalloc multiplication overflow not detected");
    if (xcalloc(2, (size_t)-1) != NULL) return fail("xcalloc multiplication overflow not detected");
    /* A request that does not overflow but cannot fit the arena must return NULL. */
    if (xcalloc(1, ALLOC_CAPACITY + 1) != NULL) return fail("xcalloc beyond capacity must return NULL");
    return 0;
}

static int sc_churn(void) {
    for (int step = 0; step < 60000; step++) {
        if (g_n < 700 && (g_n == 0 || (rnd() & 1))) {
            size_t sz = 16 + (rnd() % 2000);
            void *p = xmalloc(sz);
            if (p == NULL) continue; /* arena may legitimately be full */
            if (track(p, sz, (unsigned char)step)) return 1;
        } else if (g_n > 0) {
            int idx = (int)(rnd() % (unsigned)g_n);
            if (!pat_check(g_p[idx], g_sz[idx], g_seed[idx])) return fail("corruption detected before free");
            xfree(g_p[idx]);
            untrack(idx);
        }
        if ((step & 0x3ff) == 0)
            if (verify_all()) return 1;
    }
    return verify_all();
}

/* ---- milestone 3: coalescing, realloc, stats, fragmentation ---- */

static int sc_coalesce(void) {
    static void *blk[2000];
    int n = 0;
    for (;;) {
        void *p = xmalloc(1024);
        if (p == NULL || n >= 2000) break;
        blk[n++] = p;
    }
    if (n < 100) return fail("arena too small to exercise coalescing");
    for (int i = 0; i < n; i++) xfree(blk[i]);
    size_t big = (size_t)n * 1024u / 2u; /* far larger than any single freed block */
    unsigned char *p = (unsigned char *)xmalloc(big);
    if (p == NULL) return fail("coalescing failed: a large block did not fit after freeing all");
    if (((uintptr_t)p % ALLOC_ALIGNMENT) != 0) return fail("pointer is not 16-byte aligned");
    memset(p, 0xab, big);
    return 0;
}

static int sc_realloc_grow(void) {
    unsigned char *p = (unsigned char *)xmalloc(64);
    if (p == NULL) return fail("xmalloc(64) returned NULL");
    pat_fill(p, 64, 77);
    unsigned char *q = (unsigned char *)xrealloc(p, 4096);
    if (q == NULL) return fail("xrealloc grow returned NULL");
    if (((uintptr_t)q % ALLOC_ALIGNMENT) != 0) return fail("pointer is not 16-byte aligned");
    if (!pat_check(q, 64, 77)) return fail("xrealloc grow did not preserve the original bytes");
    return 0;
}

static int sc_realloc_shrink(void) {
    unsigned char *p = (unsigned char *)xmalloc(4096);
    if (p == NULL) return fail("xmalloc(4096) returned NULL");
    pat_fill(p, 4096, 99);
    unsigned char *q = (unsigned char *)xrealloc(p, 64);
    if (q == NULL) return fail("xrealloc shrink returned NULL");
    if (!pat_check(q, 64, 99)) return fail("xrealloc shrink did not preserve the leading bytes");
    return 0;
}

static int sc_realloc_null_zero(void) {
    void *p = xrealloc(NULL, 128);
    if (p == NULL) return fail("xrealloc(NULL, n) must behave like xmalloc(n)");
    if (((uintptr_t)p % ALLOC_ALIGNMENT) != 0) return fail("pointer is not 16-byte aligned");
    if (xrealloc(p, 0) != NULL) return fail("xrealloc(p, 0) must free and return NULL");
    return 0;
}

static int sc_realloc_fail(void) {
    /* A non-zero xrealloc that cannot be satisfied must return NULL and leave
     * the original block fully intact (not freed, not corrupted). */
    unsigned char *p = (unsigned char *)xmalloc(64);
    if (p == NULL) return fail("setup xmalloc(64) returned NULL");
    pat_fill(p, 64, 0xab);
    /* Exhaust the rest of the arena so no growth or relocation is possible. */
    static void *blk[4096];
    int n = 0;
    for (;;) {
        void *q = xmalloc(4096);
        if (q == NULL || n >= 4096) break;
        blk[n++] = q;
    }
    void *r = xrealloc(p, ALLOC_CAPACITY);
    if (r != NULL) return fail("xrealloc beyond available space must return NULL");
    /* If a buggy xrealloc freed p before failing, p's region is now reusable.
     * Drain all remaining free space with scribbling allocations; a correct
     * allocator never hands out p's still-live region, so p stays intact. */
    for (int i = 0; i < 4096; i++) {
        void *s = xmalloc(48);
        if (s == NULL) break;
        memset(s, 0xff, 48);
    }
    if (!pat_check(p, 64, 0xab)) return fail("a failed xrealloc freed or corrupted the original block");
    (void)blk;
    return 0;
}

static int sc_stats(void) {
    void *a = xmalloc(100);
    void *b = xmalloc(200);
    void *c = xmalloc(300);
    if (a == NULL || b == NULL || c == NULL) return fail("allocations for stats scenario failed");
    xfree(b);
    heap_stats_t st;
    heap_stats(&st);
    if (st.bytes_in_use != 400) {
        printf("FAIL: bytes_in_use=%zu, expected 400 (sum of live requested sizes)\n", st.bytes_in_use);
        return 1;
    }
    if (st.live_allocations != 2) {
        printf("FAIL: live_allocations=%zu, expected 2\n", st.live_allocations);
        return 1;
    }
    if (st.bytes_in_use + st.free_bytes > ALLOC_CAPACITY) return fail("bytes_in_use + free_bytes exceeds capacity");
    if (st.largest_free_block > st.free_bytes) return fail("largest_free_block exceeds free_bytes");
    /* free_bytes must reflect the genuinely available payload space, not a token
     * value. With 400 payload bytes live it should be ~capacity minus payload
     * minus a modest per-block metadata overhead (generous bound for varied
     * designs). */
    if (st.free_bytes < ALLOC_CAPACITY - 400 - 4096 || st.free_bytes > ALLOC_CAPACITY - 400) {
        printf("FAIL: free_bytes=%zu outside the expected available-space range\n", st.free_bytes);
        return 1;
    }
    /* largest_free_block must be exactly satisfiable: a request of that size
     * succeeds, and (when it is smaller than total free space) one byte more
     * does not — so the value can be neither under- nor over-reported. */
    void *proof = xmalloc(st.largest_free_block);
    if (proof == NULL) return fail("largest_free_block is reported but not actually satisfiable");
    xfree(proof);
    if (st.largest_free_block < st.free_bytes) {
        void *bigger = xmalloc(st.largest_free_block + 1);
        if (bigger != NULL) {
            xfree(bigger);
            return fail("largest_free_block is under-reported (a larger allocation succeeded)");
        }
    }
    return 0;
}

static int sc_frag(void) {
    static void *blk[5000];
    int n = 0;
    for (int i = 0; i < 5000; i++) {
        size_t sz = 16 + (size_t)((i * 48) % 2000);
        void *p = xmalloc(sz);
        if (p == NULL) break;
        blk[n++] = p;
    }
    if (n < 200) return fail("too few allocations to test fragmentation recovery");
    for (int i = 0; i < n; i++) xfree(blk[i]);
    heap_stats_t st;
    heap_stats(&st);
    if (st.live_allocations != 0) return fail("live_allocations must be 0 after freeing everything");
    size_t threshold = (ALLOC_CAPACITY / 100u) * 90u; /* 90% of capacity */
    if (st.largest_free_block < threshold) {
        printf("FAIL: largest_free_block=%zu < 90%% of capacity (%zu) — fragmentation not reclaimed\n",
               st.largest_free_block, threshold);
        return 1;
    }
    return 0;
}

struct scenario {
    const char *name;
    int (*fn)(void);
};

static const struct scenario SCENARIOS[] = {
    {"align", sc_align},
    {"integrity", sc_integrity},
    {"oom", sc_oom},
    {"zero_null", sc_zero_null},
    {"reuse", sc_reuse},
    {"split", sc_split},
    {"calloc_zero", sc_calloc_zero},
    {"calloc_overflow", sc_calloc_overflow},
    {"churn", sc_churn},
    {"coalesce", sc_coalesce},
    {"realloc_grow", sc_realloc_grow},
    {"realloc_shrink", sc_realloc_shrink},
    {"realloc_null_zero", sc_realloc_null_zero},
    {"realloc_fail", sc_realloc_fail},
    {"stats", sc_stats},
    {"frag", sc_frag},
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
