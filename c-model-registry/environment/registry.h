#ifndef REGISTRY_H
#define REGISTRY_H

#include <stddef.h>

/*
 * Model-governance registry contract.
 *
 * You implement, from scratch in C, the registry that backs a model-promotion
 * workflow for a credit-default classifier: candidate model versions are
 * registered with pre-computed evaluation metrics, evaluated against a governance
 * policy, promoted via a `champion` alias, rolled back, and persisted to disk.
 * You do not train any models — the metrics are given. You manage all memory
 * yourself with malloc/realloc/free; the registry grows as versions are added.
 *
 * The verifier compiles your registry.c together with an independent C harness
 * under UndefinedBehaviorSanitizer, so any out-of-bounds access, overflow, or
 * other undefined behavior is a hard failure. The harness drives the registry
 * with thousands of models, versions and tags through long adversarial sequences
 * of registration, tagging, promotion, rollback and save/load, and checks every
 * answer against an independent reference, so only exact results pass.
 *
 * Model names, tag keys and aliases are NUL-terminated and at most 63 bytes. Tag
 * *values* are arbitrary NUL-terminated strings of any length and may contain any
 * non-NUL byte — including spaces, newlines, colons and whatever delimiters your
 * serialization format uses — and must survive a save/load round-trip unchanged.
 */

#define REG_OK 0
#define REG_ERR 1

/* A candidate version's pre-computed evaluation record (given as input). */
typedef struct {
    double roc_auc;
    double f1_macro;
    double accuracy;
    double max_bias_dpd;        /* worst demographic-parity-difference over protected attributes */
    int uses_prohibited_proxy;  /* 1 if the candidate uses the dossier-flagged proxy feature */
} reg_metrics_t;

/* Governance-policy thresholds (from the dossier). */
typedef struct {
    double auc_floor;
    double f1_floor;
    double bias_ceiling;        /* maximum allowed max_bias_dpd */
} reg_policy_t;

/* ---- Milestone 1: register and query versions + tags ---- */

/* Register a new version of model `name` carrying metrics `m`. Versions for a
 * given name number from 1 and increment by one per registration. Returns the new
 * version number (>= 1), or 0 on allocation failure. */
int reg_register(const char *name, reg_metrics_t m);

/* Number of versions registered under `name` (0 if the name is unknown). */
int reg_version_count(const char *name);

/* Copy the metrics of (name, version) into *out. Returns REG_OK, or REG_ERR if
 * that name/version does not exist. */
int reg_get_metrics(const char *name, int version, reg_metrics_t *out);

/* Set string tag `key`=`value` on (name, version), overwriting any prior value.
 * Returns REG_OK, or REG_ERR if (name, version) does not exist. */
int reg_set_tag(const char *name, int version, const char *key, const char *value);

/* Copy the value of tag `key` on (name, version) into `buf` (capacity `buflen`,
 * always NUL-terminated on success). Returns REG_OK, or REG_ERR if the version or
 * tag is absent. */
int reg_get_tag(const char *name, int version, const char *key, char *buf, size_t buflen);

/* ---- Milestone 2: gates, aliases, promotion, rollback ---- */

/* Evaluate the promotion gate for (name, version) against `policy`: it PASSES iff
 *   roc_auc >= auc_floor AND f1_macro >= f1_floor AND
 *   max_bias_dpd <= bias_ceiling AND uses_prohibited_proxy == 0.
 * Record the result as tag "validation_status" = "passed" or "failed" on the
 * version. Returns 1 (pass), 0 (fail), or REG_ERR if the version is absent. */
int reg_evaluate_gate(const char *name, int version, reg_policy_t policy);

/* Point alias `alias` of model `name` at `version` (overwriting any prior target).
 * This is a low-level operation that does NOT touch the champion rollback history
 * (only reg_promote_champion does). Returns REG_OK, or REG_ERR if (name, version)
 * does not exist. */
int reg_set_alias(const char *name, const char *alias, int version);

/* Return the version that alias `alias` of model `name` points at, or 0 if it is
 * unset or the name is unknown. */
int reg_get_alias(const char *name, const char *alias);

/* Promote a champion: evaluate every version of `name` against `policy` (recording
 * each version's "validation_status" tag), then point the "champion" alias at the
 * PASSING version with the highest roc_auc (ties broken by highest version number).
 * All other versions remain registered and queryable. Returns the promoted version,
 * or 0 if no version passes. Each successful promotion pushes the previous champion
 * target (0 if none) onto a per-name rollback history. */
int reg_promote_champion(const char *name, reg_policy_t policy);

/* Roll the "champion" alias back to the version it pointed at before the most
 * recent reg_promote_champion call, popping the per-name promotion history that
 * reg_promote_champion builds. Only promotions are undoable — a direct
 * reg_set_alias("champion", ...) does not affect this history. Returns the
 * restored version, or 0 if there is no prior champion to roll back to (in which
 * case the champion alias becomes unset). */
int reg_rollback_champion(const char *name);

/* ---- Milestone 3: persistence ---- */

/* Serialize the entire registry — every model's versions, metrics, tags, aliases
 * and rollback history — to the file at `path`. Returns REG_OK or REG_ERR. */
int reg_save(const char *path);

/* Replace the current in-memory registry with the one stored at `path`, exactly
 * (a subsequent query must return what was saved). Returns REG_OK or REG_ERR. */
int reg_load(const char *path);

/* Empty the registry and free all memory; afterwards it is empty and reusable. */
void reg_reset(void);

#endif /* REGISTRY_H */
