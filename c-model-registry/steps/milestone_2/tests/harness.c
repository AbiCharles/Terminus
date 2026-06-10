/* Independent harness for milestone 2 (gates, aliases, promotion, rollback).
 *
 * Compiled with the candidate's registry.c under UndefinedBehaviorSanitizer. The
 * harness registers candidates with known metrics, then independently computes
 * the expected gate outcomes, the expected champion, and the expected rollback
 * behaviour, and checks the registry matches exactly.
 *
 * Usage: harness <scenario>
 */
#include "registry.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned long rng = 2463534242UL;
static double rnd(double a, double b) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return a + (b - a) * ((double)(rng >> 11) / 9007199254740992.0);
}
static int rint_(int n) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (int)((rng >> 11) % (unsigned)n); }

static int gate_pass(reg_metrics_t m, reg_policy_t p) {
    return m.roc_auc >= p.auc_floor && m.f1_macro >= p.f1_floor &&
           m.max_bias_dpd <= p.bias_ceiling && m.uses_prohibited_proxy == 0;
}

static int sc_gates(void) {
    reg_policy_t p = {0.85, 0.75, 0.10};
    reg_metrics_t mv[200];
    for (int v = 1; v <= 200; v++) {
        reg_metrics_t m = {rnd(0.7, 0.99), rnd(0.6, 0.95), rnd(0.7, 0.95), rnd(0.0, 0.20), rint_(5) == 0 ? 1 : 0};
        mv[v - 1] = m;
        reg_register("m", m);
    }
    char buf[64];
    for (int v = 1; v <= 200; v++) {
        int exp = gate_pass(mv[v - 1], p);
        int got = reg_evaluate_gate("m", v, p);
        if (got != exp) { printf("FAIL gate v%d got=%d exp=%d\n", v, got, exp); return 1; }
        if (reg_get_tag("m", v, "validation_status", buf, sizeof buf) != REG_OK) { printf("FAIL no status tag\n"); return 1; }
        if (strcmp(buf, exp ? "passed" : "failed")) { printf("FAIL status tag v%d=%s\n", v, buf); return 1; }
    }
    if (reg_evaluate_gate("m", 999, p) != REG_ERR) { printf("FAIL gate absent\n"); return 1; }
    return 0;
}

static int sc_aliases(void) {
    for (int v = 1; v <= 5; v++) reg_register("m", (reg_metrics_t){0.9, 0.8, 0.85, 0.05, 0});
    if (reg_get_alias("m", "staging") != 0) { printf("FAIL unset alias\n"); return 1; }
    if (reg_set_alias("m", "staging", 3) != REG_OK || reg_get_alias("m", "staging") != 3) { printf("FAIL set alias\n"); return 1; }
    if (reg_set_alias("m", "staging", 5) != REG_OK || reg_get_alias("m", "staging") != 5) { printf("FAIL move alias\n"); return 1; }
    if (reg_set_alias("m", "prod", 1) != REG_OK || reg_get_alias("m", "staging") != 5 || reg_get_alias("m", "prod") != 1) { printf("FAIL two aliases\n"); return 1; }
    if (reg_set_alias("m", "x", 99) != REG_ERR) { printf("FAIL alias absent version\n"); return 1; }
    if (reg_get_alias("unknown", "staging") != 0) { printf("FAIL alias unknown model\n"); return 1; }
    return 0;
}

/* expected champion = highest-roc_auc passing version (ties: highest version) */
static int expected_champion(reg_metrics_t *mv, int n, reg_policy_t p) {
    int best = 0; double ba = -1;
    for (int v = 1; v <= n; v++) if (gate_pass(mv[v - 1], p)) {
        double a = mv[v - 1].roc_auc;
        if (a > ba || (a == ba && v > best)) { ba = a; best = v; }
    }
    return best;
}

static int sc_promote(void) {
    reg_policy_t p = {0.85, 0.75, 0.10};
    reg_metrics_t mv[40]; int n = 0;
    /* ensure at least one passing */
    mv[n++] = (reg_metrics_t){0.91, 0.82, 0.88, 0.04, 0};
    for (int i = 1; i < 30; i++) mv[n++] = (reg_metrics_t){rnd(0.7, 0.99), rnd(0.6, 0.95), rnd(0.7, 0.95), rnd(0.0, 0.20), rint_(5) == 0 ? 1 : 0};
    for (int v = 1; v <= n; v++) reg_register("m", mv[v - 1]);
    int exp = expected_champion(mv, n, p);
    int got = reg_promote_champion("m", p);
    if (got != exp) { printf("FAIL promote got=%d exp=%d\n", got, exp); return 1; }
    if (reg_get_alias("m", "champion") != exp) { printf("FAIL champion alias\n"); return 1; }
    /* all-fail model promotes to nothing */
    reg_register("bad", (reg_metrics_t){0.5, 0.5, 0.5, 0.9, 1});
    if (reg_promote_champion("bad", p) != 0) { printf("FAIL promote-none\n"); return 1; }
    if (reg_get_alias("bad", "champion") != 0) { printf("FAIL champion-none\n"); return 1; }
    return 0;
}

/* many promote/rollback cycles: champion alias must follow the history stack */
static int sc_rollback_deep(void) {
    reg_policy_t p = {0.80, 0.70, 0.20};
    int champ_hist[512]; int top = 0;      /* simulated rollback stack of PREVIOUS targets */
    int cur_champ = 0;
    int n = 0; reg_metrics_t mv[600];
    for (int step = 0; step < 300; step++) {
        if (rint_(3) != 0 || n == 0) {
            /* register a new (always-passing) candidate, then promote */
            reg_metrics_t m = {rnd(0.85, 0.99), 0.9, 0.9, 0.02, 0};
            mv[n++] = m; reg_register("m", m);
            int exp = expected_champion(mv, n, p);
            int got = reg_promote_champion("m", p);
            if (got != exp) { printf("FAIL deep promote step%d got=%d exp=%d\n", step, got, exp); return 1; }
            champ_hist[top++] = cur_champ;   /* promotion pushes previous champion */
            cur_champ = exp;
            if (reg_get_alias("m", "champion") != cur_champ) { printf("FAIL deep champ step%d\n", step); return 1; }
        } else {
            /* rollback */
            int got = reg_rollback_champion("m");
            int prev = top > 0 ? champ_hist[--top] : 0;
            int exp = prev;  /* restored target (0 => unset) */
            if (got != exp) { printf("FAIL deep rollback step%d got=%d exp=%d\n", step, got, exp); return 1; }
            cur_champ = prev;
            if (reg_get_alias("m", "champion") != cur_champ) { printf("FAIL deep rollback alias step%d got=%d exp=%d\n", step, reg_get_alias("m", "champion"), cur_champ); return 1; }
        }
    }
    return 0;
}

/* tie-break: several gate-passing versions share the highest roc_auc -> the
 * champion is the highest version among them. */
static int sc_promote_ties(void) {
    reg_policy_t p = {0.80, 0.70, 0.20};
    reg_metrics_t mv[6] = {
        {0.90, 0.8, 0.85, 0.05, 0},
        {0.95, 0.8, 0.85, 0.05, 0},   /* tie for max auc */
        {0.92, 0.8, 0.85, 0.05, 0},
        {0.95, 0.8, 0.85, 0.05, 0},   /* tie for max auc, higher version -> champion */
        {0.93, 0.8, 0.85, 0.05, 0},
        {0.50, 0.8, 0.85, 0.05, 0},   /* fails auc */
    };
    for (int v = 1; v <= 6; v++) reg_register("m", mv[v - 1]);
    int got = reg_promote_champion("m", p);
    if (got != 4) { printf("FAIL tie champion got=%d exp=4\n", got); return 1; }
    if (reg_get_alias("m", "champion") != 4) { printf("FAIL tie alias\n"); return 1; }
    return 0;
}

/* promotion must record validation_status on EVERY version it evaluates. */
static int sc_gate_records_all(void) {
    reg_policy_t p = {0.85, 0.75, 0.10};
    reg_metrics_t mv[6] = {
        {0.90, 0.80, 0.85, 0.05, 0},  /* pass */
        {0.70, 0.80, 0.85, 0.05, 0},  /* fail auc */
        {0.95, 0.60, 0.85, 0.05, 0},  /* fail f1 */
        {0.95, 0.80, 0.85, 0.50, 0},  /* fail bias */
        {0.95, 0.80, 0.85, 0.05, 1},  /* fail proxy */
        {0.99, 0.90, 0.92, 0.02, 0},  /* pass (best) */
    };
    int exp[6] = {1, 0, 0, 0, 0, 1};
    for (int v = 1; v <= 6; v++) reg_register("m", mv[v - 1]);
    if (reg_promote_champion("m", p) != 6) { printf("FAIL gate-all champion\n"); return 1; }
    char buf[32];
    for (int v = 1; v <= 6; v++) {
        if (reg_get_tag("m", v, "validation_status", buf, sizeof buf) != REG_OK) { printf("FAIL no status v%d\n", v); return 1; }
        if (strcmp(buf, exp[v - 1] ? "passed" : "failed")) { printf("FAIL status v%d=%s\n", v, buf); return 1; }
    }
    return 0;
}

/* each model keeps an INDEPENDENT champion history; interleave promote/rollback
 * across several models and check every champion alias stays correct. */
static int sc_multi_model_rollback(void) {
    reg_policy_t p = {0.80, 0.70, 0.20};
    int champ[5] = {0, 0, 0, 0, 0};
    int hist[5][128]; int top[5] = {0, 0, 0, 0, 0};
    int nver[5] = {0, 0, 0, 0, 0};
    char nm[16];
    for (int step = 0; step < 500; step++) {
        int mdl = rint_(5);
        snprintf(nm, sizeof nm, "m%d", mdl);
        if (rint_(3) != 0 || nver[mdl] == 0) {
            reg_register(nm, (reg_metrics_t){0.85 + 0.001 * nver[mdl], 0.9, 0.9, 0.02, 0});  /* new = best */
            nver[mdl]++;
            int exp = nver[mdl];
            int got = reg_promote_champion(nm, p);
            if (got != exp) { printf("FAIL multi promote m%d step%d got=%d exp=%d\n", mdl, step, got, exp); return 1; }
            hist[mdl][top[mdl]++] = champ[mdl];
            champ[mdl] = exp;
        } else {
            int got = reg_rollback_champion(nm);
            int prev = top[mdl] > 0 ? hist[mdl][--top[mdl]] : 0;
            if (got != prev) { printf("FAIL multi rollback m%d step%d got=%d exp=%d\n", mdl, step, got, prev); return 1; }
            champ[mdl] = prev;
        }
        if (reg_get_alias(nm, "champion") != champ[mdl]) { printf("FAIL multi champ m%d step%d got=%d exp=%d\n", mdl, step, reg_get_alias(nm, "champion"), champ[mdl]); return 1; }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) { printf("usage: harness <scenario>\n"); return 2; }
    reg_reset();
    const char *s = argv[1];
    int rc;
    if (!strcmp(s, "gates")) rc = sc_gates();
    else if (!strcmp(s, "aliases")) rc = sc_aliases();
    else if (!strcmp(s, "promote")) rc = sc_promote();
    else if (!strcmp(s, "rollback_deep")) rc = sc_rollback_deep();
    else if (!strcmp(s, "promote_ties")) rc = sc_promote_ties();
    else if (!strcmp(s, "gate_records_all")) rc = sc_gate_records_all();
    else if (!strcmp(s, "multi_model_rollback")) rc = sc_multi_model_rollback();
    else { printf("unknown scenario %s\n", s); return 2; }
    if (rc == 0) printf("OK\n");
    return rc;
}
