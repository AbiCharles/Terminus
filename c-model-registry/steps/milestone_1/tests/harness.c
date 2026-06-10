/* Independent harness for milestone 1 (register + query versions + tags).
 *
 * Compiled with the candidate's registry.c under UndefinedBehaviorSanitizer.
 * Models are named model_<i> and carry metrics derived deterministically from
 * (i, version), so the harness verifies the registry's answers without keeping a
 * parallel store. Each scenario prints "OK" and exits 0 on success; a wrong answer
 * or a sanitizer abort yields a non-zero exit. The scale scenario stresses the
 * nested storage and tag handling with thousands of models, versions and tags.
 *
 * Usage: harness <scenario>
 */
#include "registry.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static reg_metrics_t mk(int i, int v) {
    reg_metrics_t m;
    m.roc_auc = 0.50 + (double)((i * 7 + v * 13) % 50) / 100.0;
    m.f1_macro = 0.40 + (double)((i * 11 + v * 5) % 55) / 100.0;
    m.accuracy = 0.60 + (double)((i * 3 + v) % 40) / 100.0;
    m.max_bias_dpd = (double)((i + v) % 25) / 100.0;
    m.uses_prohibited_proxy = ((i + v) % 7 == 0) ? 1 : 0;
    return m;
}
static int eq(reg_metrics_t a, reg_metrics_t b) {
    return a.roc_auc == b.roc_auc && a.f1_macro == b.f1_macro && a.accuracy == b.accuracy &&
           a.max_bias_dpd == b.max_bias_dpd && a.uses_prohibited_proxy == b.uses_prohibited_proxy;
}
static unsigned long rng = 88172645463325252UL;
static int rint(int n) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (int)((rng >> 11) % (unsigned)n); }

static int sc_basic(void) {
    char name[64];
    for (int i = 0; i < 50; i++) {
        snprintf(name, sizeof(name), "model_%d", i);
        int nv = 1 + (i % 4);
        for (int v = 1; v <= nv; v++)
            if (reg_register(name, mk(i, v)) != v) { printf("FAIL register %s v%d\n", name, v); return 1; }
        if (reg_version_count(name) != nv) { printf("FAIL count %s\n", name); return 1; }
    }
    if (reg_version_count("model_999") != 0) { printf("FAIL unknown count\n"); return 1; }
    for (int i = 0; i < 50; i++) {
        snprintf(name, sizeof(name), "model_%d", i);
        int nv = 1 + (i % 4);
        for (int v = 1; v <= nv; v++) {
            reg_metrics_t got;
            if (reg_get_metrics(name, v, &got) != REG_OK || !eq(got, mk(i, v))) { printf("FAIL get %s v%d\n", name, v); return 1; }
        }
        reg_metrics_t got;
        if (reg_get_metrics(name, nv + 1, &got) != REG_ERR) { printf("FAIL get absent version\n"); return 1; }
    }
    return 0;
}

static int sc_tags(void) {
    reg_register("m", mk(1, 1)); reg_register("m", mk(1, 2));
    char buf[128];
    if (reg_set_tag("m", 1, "owner", "risk") != REG_OK) { printf("FAIL settag\n"); return 1; }
    if (reg_set_tag("m", 1, "stage", "dev") != REG_OK) { printf("FAIL settag2\n"); return 1; }
    if (reg_get_tag("m", 1, "owner", buf, sizeof buf) != REG_OK || strcmp(buf, "risk")) { printf("FAIL gettag\n"); return 1; }
    if (reg_set_tag("m", 1, "owner", "ml-platform-team") != REG_OK) { printf("FAIL overwrite\n"); return 1; }
    if (reg_get_tag("m", 1, "owner", buf, sizeof buf) != REG_OK || strcmp(buf, "ml-platform-team")) { printf("FAIL overwrite-get\n"); return 1; }
    if (reg_get_tag("m", 1, "missing", buf, sizeof buf) != REG_ERR) { printf("FAIL tag-absent\n"); return 1; }
    if (reg_get_tag("m", 2, "owner", buf, sizeof buf) != REG_ERR) { printf("FAIL tag-other-version\n"); return 1; }
    if (reg_set_tag("nope", 1, "k", "v") != REG_ERR) { printf("FAIL tag-absent-model\n"); return 1; }
    return 0;
}

static int sc_reset(void) {
    char name[64];
    for (int i = 0; i < 2000; i++) { snprintf(name, sizeof(name), "model_%d", i); reg_register(name, mk(i, 1)); reg_set_tag(name, 1, "k", "v"); }
    if (reg_version_count("model_1500") != 1) { printf("FAIL pre-reset\n"); return 1; }
    reg_reset();
    if (reg_version_count("model_1500") != 0) { printf("FAIL after reset\n"); return 1; }
    for (int i = 0; i < 1000; i++) { snprintf(name, sizeof(name), "fresh_%d", i); reg_register(name, mk(i, 1)); }
    reg_metrics_t got;
    if (reg_get_metrics("fresh_500", 1, &got) != REG_OK || !eq(got, mk(500, 1))) { printf("FAIL reuse\n"); return 1; }
    return 0;
}

/* large registry: a linear scan over models on each register/lookup times out. */
static int sc_scale(void) {
    int N = 5000;
    char name[64];
    for (int i = 0; i < N; i++) {
        snprintf(name, sizeof(name), "model_%d", i);
        for (int v = 1; v <= 4; v++) reg_register(name, mk(i, v));
        reg_set_tag(name, 1, "team", "alpha");
    }
    for (int q = 0; q < 200000; q++) {
        int i = rint(N), v = 1 + rint(4);
        snprintf(name, sizeof(name), "model_%d", i);
        reg_metrics_t got;
        if (q % 5000 == 0) {  /* full check on a sample; the rest exercises lookup speed */
            if (reg_version_count(name) != 4) { printf("FAIL scale count\n"); return 1; }
            if (reg_get_metrics(name, v, &got) != REG_OK || !eq(got, mk(i, v))) { printf("FAIL scale get\n"); return 1; }
            char buf[64];
            if (reg_get_tag(name, 1, "team", buf, sizeof buf) != REG_OK || strcmp(buf, "alpha")) { printf("FAIL scale tag\n"); return 1; }
        } else {
            reg_get_metrics(name, v, &got);
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { printf("usage: harness <scenario>\n"); return 2; }
    reg_reset();
    const char *s = argv[1];
    int rc;
    if (!strcmp(s, "basic")) rc = sc_basic();
    else if (!strcmp(s, "tags")) rc = sc_tags();
    else if (!strcmp(s, "reset")) rc = sc_reset();
    else if (!strcmp(s, "scale")) rc = sc_scale();
    else { printf("unknown scenario %s\n", s); return 2; }
    if (rc == 0) printf("OK\n");
    return rc;
}
