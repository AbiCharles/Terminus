/* Independent harness for milestone 3 (persistence / save-load round-trip).
 *
 * Compiled with the candidate's registry.c under UndefinedBehaviorSanitizer.
 * Builds a registry, saves it, resets, loads it back, and verifies that every
 * model, version, metric, tag (including values with newlines, colons, spaces and
 * other delimiters), alias and rollback-history entry survives exactly. Tag values
 * are arbitrary bytes, so a naive key=value/line-based format will not round-trip.
 *
 * Usage: harness <scenario>
 */
#include "registry.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SNAP "/tmp/reg_snapshot.bin"

static unsigned long rng = 0x9e3779b97f4a7c15UL;
static int rint_(int n) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (int)((rng >> 11) % (unsigned)n); }

static reg_metrics_t mk(int s) {
    return (reg_metrics_t){0.5 + (s % 50) / 100.0, 0.4 + (s % 40) / 100.0, 0.6 + (s % 30) / 100.0, (s % 20) / 100.0, (s % 6 == 0)};
}
static int eqm(reg_metrics_t a, reg_metrics_t b) {
    return a.roc_auc == b.roc_auc && a.f1_macro == b.f1_macro && a.accuracy == b.accuracy &&
           a.max_bias_dpd == b.max_bias_dpd && a.uses_prohibited_proxy == b.uses_prohibited_proxy;
}

static int sc_roundtrip(void) {
    char name[64], key[64];
    int NM = 300;
    for (int i = 0; i < NM; i++) {
        snprintf(name, sizeof(name), "model_%d", i);
        int nv = 1 + (i % 5);
        for (int v = 1; v <= nv; v++) {
            reg_register(name, mk(i * 31 + v));
            int nt = i % 3;
            for (int t = 0; t < nt; t++) {
                snprintf(key, sizeof(key), "tag_%d", t);
                char val[64]; snprintf(val, sizeof(val), "value_%d_%d", i, v);
                reg_set_tag(name, v, key, val);
            }
        }
        if (i % 2 == 0) reg_set_alias(name, "champion", 1 + (i % nv));
    }
    if (reg_save(SNAP) != REG_OK) { printf("FAIL save\n"); return 1; }
    reg_reset();
    if (reg_version_count("model_5") != 0) { printf("FAIL reset before load\n"); return 1; }
    if (reg_load(SNAP) != REG_OK) { printf("FAIL load\n"); return 1; }
    for (int i = 0; i < NM; i++) {
        snprintf(name, sizeof(name), "model_%d", i);
        int nv = 1 + (i % 5);
        if (reg_version_count(name) != nv) { printf("FAIL count %s after load\n", name); return 1; }
        for (int v = 1; v <= nv; v++) {
            reg_metrics_t got;
            if (reg_get_metrics(name, v, &got) != REG_OK || !eqm(got, mk(i * 31 + v))) { printf("FAIL metrics %s v%d\n", name, v); return 1; }
            int nt = i % 3;
            for (int t = 0; t < nt; t++) {
                snprintf(key, sizeof(key), "tag_%d", t);
                char val[64], buf[64]; snprintf(val, sizeof(val), "value_%d_%d", i, v);
                if (reg_get_tag(name, v, key, buf, sizeof buf) != REG_OK || strcmp(buf, val)) { printf("FAIL tag %s v%d %s\n", name, v, key); return 1; }
            }
        }
        if (i % 2 == 0 && reg_get_alias(name, "champion") != 1 + (i % nv)) { printf("FAIL alias %s after load\n", name); return 1; }
    }
    return 0;
}

/* tag values containing the bytes a serialization format is tempted to use as
 * delimiters: newlines, colons, spaces, equals, quotes, empty, and a long value. */
static int sc_adversarial_strings(void) {
    const char *vals[] = {
        "plain",
        "with spaces and\ttabs",
        "line1\nline2\nline3",
        "key:value:pairs:everywhere",
        "k=v&other=thing",
        "quoted \"value\" and 'apostrophe'",
        "",                                   /* empty value */
        "trailing-newline\n",
        "json-ish {\"a\": 1, \"b\": [2,3]}",
    };
    int NV = (int)(sizeof(vals) / sizeof(vals[0]));
    /* also a very long value */
    static char longv[5000];
    for (int i = 0; i < 4999; i++) longv[i] = (char)('!' + (i % 90));
    longv[4999] = '\0';
    reg_register("m", mk(1));
    char key[32];
    for (int i = 0; i < NV; i++) { snprintf(key, sizeof key, "k%d", i); reg_set_tag("m", 1, key, vals[i]); }
    reg_set_tag("m", 1, "klong", longv);
    if (reg_save(SNAP) != REG_OK) { printf("FAIL save\n"); return 1; }
    reg_reset();
    if (reg_load(SNAP) != REG_OK) { printf("FAIL load\n"); return 1; }
    static char buf[8192];
    for (int i = 0; i < NV; i++) {
        snprintf(key, sizeof key, "k%d", i);
        if (reg_get_tag("m", 1, key, buf, sizeof buf) != REG_OK) { printf("FAIL get %s\n", key); return 1; }
        if (strcmp(buf, vals[i])) { printf("FAIL roundtrip value k%d: got len %zu\n", i, strlen(buf)); return 1; }
    }
    if (reg_get_tag("m", 1, "klong", buf, sizeof buf) != REG_OK || strcmp(buf, longv)) { printf("FAIL long value roundtrip\n"); return 1; }
    return 0;
}

/* rollback history must survive save/load: after loading, rollback still works */
static int sc_state_roundtrip(void) {
    reg_policy_t p = {0.80, 0.70, 0.20};
    for (int v = 1; v <= 4; v++) reg_register("m", (reg_metrics_t){0.85 + v * 0.02, 0.9, 0.9, 0.02, 0});
    reg_promote_champion("m", p);      /* champion -> v4 (highest auc), history [0] */
    reg_register("m", (reg_metrics_t){0.80, 0.9, 0.9, 0.02, 0});  /* v5, lower auc */
    reg_promote_champion("m", p);      /* champion still v4 (best), history [0,4] */
    int champ_before = reg_get_alias("m", "champion");
    if (reg_save(SNAP) != REG_OK) { printf("FAIL save\n"); return 1; }
    reg_reset();
    if (reg_load(SNAP) != REG_OK) { printf("FAIL load\n"); return 1; }
    if (reg_get_alias("m", "champion") != champ_before) { printf("FAIL champ after load\n"); return 1; }
    /* rollback history preserved: two rollbacks should pop [4] then [0] */
    int r1 = reg_rollback_champion("m");
    if (r1 != 4) { printf("FAIL rollback1 after load got=%d\n", r1); return 1; }
    int r2 = reg_rollback_champion("m");
    if (r2 != 0 || reg_get_alias("m", "champion") != 0) { printf("FAIL rollback2 after load got=%d\n", r2); return 1; }
    return 0;
}

/* load replaces whatever is in memory */
static int sc_load_replaces(void) {
    for (int v = 1; v <= 3; v++) reg_register("a", mk(v));
    reg_save(SNAP);
    reg_reset();
    for (int v = 1; v <= 7; v++) reg_register("b", mk(v));   /* different content */
    if (reg_load(SNAP) != REG_OK) { printf("FAIL load\n"); return 1; }
    if (reg_version_count("b") != 0) { printf("FAIL old content survived load\n"); return 1; }
    if (reg_version_count("a") != 3) { printf("FAIL loaded content missing\n"); return 1; }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { printf("usage: harness <scenario>\n"); return 2; }
    reg_reset();
    const char *s = argv[1];
    int rc;
    if (!strcmp(s, "roundtrip")) rc = sc_roundtrip();
    else if (!strcmp(s, "adversarial_strings")) rc = sc_adversarial_strings();
    else if (!strcmp(s, "state_roundtrip")) rc = sc_state_roundtrip();
    else if (!strcmp(s, "load_replaces")) rc = sc_load_replaces();
    else { printf("unknown scenario %s\n", s); return 2; }
    if (rc == 0) printf("OK\n");
    return rc;
}
