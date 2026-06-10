#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: write the complete registry implementation to /app/registry.c
# (it satisfies all milestones; the verifier compiles it with the milestone's harness
# under UBSan). Self-contained across milestones.
cat > /app/registry.c <<'REGISTRY_EOF'
/* Reference model-governance registry: name -> Model via an open-addressing hash
 * map; each Model holds a dynamic version array, a dynamic alias array, and a
 * champion rollback-history stack; each Version holds metrics and a dynamic tag
 * array with heap-allocated values. Persistence uses a length-prefixed text
 * format that round-trips exactly. */
#include "registry.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char key[64]; char *val; } Tag;
typedef struct { reg_metrics_t m; Tag *tags; size_t ntags, captags; } Version;
typedef struct { char alias[64]; int version; } Alias;
typedef struct {
    char name[64];
    Version *vers; size_t nver, capver;
    Alias *al; size_t nal, capal;
    int *rb; size_t nrb, caprb;     /* champion rollback history (previous targets) */
} Model;

static Model *g_models = NULL;
static size_t g_nmodels = 0, g_capmodels = 0;
/* hash map: name -> model index */
static long *g_hk = NULL;           /* hash slot -> model index, or -1 */
static size_t g_hcap = 0;

static unsigned long strhash(const char *s) {
    unsigned long h = 1469598103934665603UL;
    for (; *s; s++) { h ^= (unsigned char)*s; h *= 1099511628211UL; }
    return h;
}

static void hmap_grow(void) {
    size_t nc = g_hcap ? g_hcap * 2 : 1024;
    long *nk = malloc(nc * sizeof(long));
    for (size_t i = 0; i < nc; i++) nk[i] = -1;
    for (size_t i = 0; i < g_hcap; i++) {
        if (g_hk[i] < 0) continue;
        size_t h = strhash(g_models[g_hk[i]].name) & (nc - 1);
        while (nk[h] != -1) h = (h + 1) & (nc - 1);
        nk[h] = g_hk[i];
    }
    free(g_hk); g_hk = nk; g_hcap = nc;
}

static long find_model(const char *name) {
    if (!g_hcap) return -1;
    size_t h = strhash(name) & (g_hcap - 1);
    while (g_hk[h] != -1) {
        if (strcmp(g_models[g_hk[h]].name, name) == 0) return g_hk[h];
        h = (h + 1) & (g_hcap - 1);
    }
    return -1;
}

static long get_or_add_model(const char *name) {
    long idx = find_model(name);
    if (idx >= 0) return idx;
    if ((g_nmodels + 1) * 2 >= g_hcap) hmap_grow();
    if (g_nmodels == g_capmodels) {
        g_capmodels = g_capmodels ? g_capmodels * 2 : 64;
        g_models = realloc(g_models, g_capmodels * sizeof(Model));
    }
    Model *m = &g_models[g_nmodels];
    memset(m, 0, sizeof(*m));
    snprintf(m->name, sizeof(m->name), "%s", name);
    idx = (long)g_nmodels++;
    size_t h = strhash(name) & (g_hcap - 1);
    while (g_hk[h] != -1) h = (h + 1) & (g_hcap - 1);
    g_hk[h] = idx;
    return idx;
}

int reg_register(const char *name, reg_metrics_t mm) {
    long idx = get_or_add_model(name);
    Model *m = &g_models[idx];
    if (m->nver == m->capver) {
        m->capver = m->capver ? m->capver * 2 : 4;
        m->vers = realloc(m->vers, m->capver * sizeof(Version));
    }
    Version *v = &m->vers[m->nver];
    v->m = mm; v->tags = NULL; v->ntags = 0; v->captags = 0;
    m->nver++;
    return (int)m->nver;  /* versions number from 1 */
}

int reg_version_count(const char *name) {
    long idx = find_model(name);
    return idx < 0 ? 0 : (int)g_models[idx].nver;
}

static Version *get_version(const char *name, int version) {
    long idx = find_model(name);
    if (idx < 0) return NULL;
    Model *m = &g_models[idx];
    if (version < 1 || (size_t)version > m->nver) return NULL;
    return &m->vers[version - 1];
}

int reg_get_metrics(const char *name, int version, reg_metrics_t *out) {
    Version *v = get_version(name, version);
    if (!v) return REG_ERR;
    *out = v->m;
    return REG_OK;
}

static Tag *find_tag(Version *v, const char *key) {
    for (size_t i = 0; i < v->ntags; i++) if (strcmp(v->tags[i].key, key) == 0) return &v->tags[i];
    return NULL;
}

int reg_set_tag(const char *name, int version, const char *key, const char *value) {
    Version *v = get_version(name, version);
    if (!v) return REG_ERR;
    Tag *t = find_tag(v, key);
    if (!t) {
        if (v->ntags == v->captags) { v->captags = v->captags ? v->captags * 2 : 4; v->tags = realloc(v->tags, v->captags * sizeof(Tag)); }
        t = &v->tags[v->ntags++];
        snprintf(t->key, sizeof(t->key), "%s", key);
        t->val = NULL;
    }
    char *nv = malloc(strlen(value) + 1);
    strcpy(nv, value);
    free(t->val);
    t->val = nv;
    return REG_OK;
}

int reg_get_tag(const char *name, int version, const char *key, char *buf, size_t buflen) {
    Version *v = get_version(name, version);
    if (!v) return REG_ERR;
    Tag *t = find_tag(v, key);
    if (!t) return REG_ERR;
    snprintf(buf, buflen, "%s", t->val);
    return REG_OK;
}

int reg_evaluate_gate(const char *name, int version, reg_policy_t p) {
    Version *v = get_version(name, version);
    if (!v) return REG_ERR;
    int pass = (v->m.roc_auc >= p.auc_floor) && (v->m.f1_macro >= p.f1_floor) &&
               (v->m.max_bias_dpd <= p.bias_ceiling) && (v->m.uses_prohibited_proxy == 0);
    reg_set_tag(name, version, "validation_status", pass ? "passed" : "failed");
    return pass ? 1 : 0;
}

static Alias *find_alias(Model *m, const char *alias) {
    for (size_t i = 0; i < m->nal; i++) if (strcmp(m->al[i].alias, alias) == 0) return &m->al[i];
    return NULL;
}
static void put_alias(Model *m, const char *alias, int version) {
    Alias *a = find_alias(m, alias);
    if (!a) {
        if (m->nal == m->capal) { m->capal = m->capal ? m->capal * 2 : 4; m->al = realloc(m->al, m->capal * sizeof(Alias)); }
        a = &m->al[m->nal++];
        snprintf(a->alias, sizeof(a->alias), "%s", alias);
    }
    a->version = version;
}

int reg_set_alias(const char *name, const char *alias, int version) {
    if (!get_version(name, version)) return REG_ERR;
    put_alias(&g_models[find_model(name)], alias, version);
    return REG_OK;
}

int reg_get_alias(const char *name, const char *alias) {
    long idx = find_model(name);
    if (idx < 0) return 0;
    Alias *a = find_alias(&g_models[idx], alias);
    return a ? a->version : 0;
}

int reg_promote_champion(const char *name, reg_policy_t p) {
    long idx = find_model(name);
    if (idx < 0) return 0;
    Model *m = &g_models[idx];
    int best = 0; double best_auc = -1.0;
    for (size_t i = 0; i < m->nver; i++) {
        int pass = reg_evaluate_gate(name, (int)i + 1, p);
        if (pass == 1) {
            double auc = m->vers[i].m.roc_auc;
            if (auc > best_auc || (auc == best_auc && (int)i + 1 > best)) { best_auc = auc; best = (int)i + 1; }
        }
    }
    if (best == 0) return 0;
    Alias *a = find_alias(m, "champion");
    int prev = a ? a->version : 0;
    if (m->nrb == m->caprb) { m->caprb = m->caprb ? m->caprb * 2 : 4; m->rb = realloc(m->rb, m->caprb * sizeof(int)); }
    m->rb[m->nrb++] = prev;
    put_alias(m, "champion", best);
    return best;
}

int reg_rollback_champion(const char *name) {
    long idx = find_model(name);
    if (idx < 0) return 0;
    Model *m = &g_models[idx];
    if (m->nrb == 0) return 0;
    int prev = m->rb[--m->nrb];
    if (prev == 0) {
        /* unset the champion alias */
        Alias *a = find_alias(m, "champion");
        if (a) { *a = m->al[--m->nal]; }
        return 0;
    }
    put_alias(m, "champion", prev);
    return prev;
}

static void wstr(FILE *f, const char *s) { fprintf(f, "%zu:", strlen(s)); fwrite(s, 1, strlen(s), f); fputc('\n', f); }
static char *rstr(FILE *f) {
    size_t n; if (fscanf(f, "%zu:", &n) != 1) return NULL;
    char *s = malloc(n + 1); if (fread(s, 1, n, f) != n) { free(s); return NULL; }
    s[n] = '\0'; fgetc(f); return s;
}

int reg_save(const char *path) {
    FILE *f = fopen(path, "w");
    if (!f) return REG_ERR;
    fprintf(f, "%zu\n", g_nmodels);
    for (size_t i = 0; i < g_nmodels; i++) {
        Model *m = &g_models[i];
        wstr(f, m->name);
        fprintf(f, "%zu %zu %zu\n", m->nver, m->nal, m->nrb);
        for (size_t v = 0; v < m->nver; v++) {
            reg_metrics_t *mm = &m->vers[v].m;
            fprintf(f, "%.17g %.17g %.17g %.17g %d %zu\n", mm->roc_auc, mm->f1_macro, mm->accuracy,
                    mm->max_bias_dpd, mm->uses_prohibited_proxy, m->vers[v].ntags);
            for (size_t t = 0; t < m->vers[v].ntags; t++) { wstr(f, m->vers[v].tags[t].key); wstr(f, m->vers[v].tags[t].val); }
        }
        for (size_t a = 0; a < m->nal; a++) { wstr(f, m->al[a].alias); fprintf(f, "%d\n", m->al[a].version); }
        for (size_t r = 0; r < m->nrb; r++) fprintf(f, "%d\n", m->rb[r]);
    }
    fclose(f);
    return REG_OK;
}

int reg_load(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) return REG_ERR;
    reg_reset();
    size_t nm; if (fscanf(f, "%zu\n", &nm) != 1) { fclose(f); return REG_ERR; }
    for (size_t i = 0; i < nm; i++) {
        char *name = rstr(f);
        long idx = get_or_add_model(name); free(name);
        Model *m = &g_models[idx];
        size_t nver, nal, nrb; if (fscanf(f, "%zu %zu %zu\n", &nver, &nal, &nrb) != 3) { fclose(f); return REG_ERR; }
        for (size_t v = 0; v < nver; v++) {
            reg_metrics_t mm; size_t ntags;
            if (fscanf(f, "%lf %lf %lf %lf %d %zu\n", &mm.roc_auc, &mm.f1_macro, &mm.accuracy, &mm.max_bias_dpd, &mm.uses_prohibited_proxy, &ntags) != 6) { fclose(f); return REG_ERR; }
            reg_register(m->name, mm);
            for (size_t t = 0; t < ntags; t++) { char *k = rstr(f), *vv = rstr(f); reg_set_tag(m->name, (int)v + 1, k, vv); free(k); free(vv); }
        }
        for (size_t a = 0; a < nal; a++) { char *al = rstr(f); int ver; if (fscanf(f, "%d\n", &ver) != 1) { free(al); fclose(f); return REG_ERR; } put_alias(m, al, ver); free(al); }
        for (size_t r = 0; r < nrb; r++) { int rv; if (fscanf(f, "%d\n", &rv) != 1) { fclose(f); return REG_ERR; } if (m->nrb == m->caprb) { m->caprb = m->caprb ? m->caprb * 2 : 4; m->rb = realloc(m->rb, m->caprb * sizeof(int)); } m->rb[m->nrb++] = rv; }
    }
    fclose(f);
    return REG_OK;
}

void reg_reset(void) {
    for (size_t i = 0; i < g_nmodels; i++) {
        Model *m = &g_models[i];
        for (size_t v = 0; v < m->nver; v++) { for (size_t t = 0; t < m->vers[v].ntags; t++) free(m->vers[v].tags[t].val); free(m->vers[v].tags); }
        free(m->vers); free(m->al); free(m->rb);
    }
    free(g_models); g_models = NULL; g_nmodels = 0; g_capmodels = 0;
    free(g_hk); g_hk = NULL; g_hcap = 0;
}
REGISTRY_EOF

gcc -std=c11 -O2 -fsanitize=undefined -I/app -c /app/registry.c -o /tmp/registry.o
echo " wrote and compiled /app/registry.c (milestone 3)"
