#include "registry.h"

/*
 * Starting stub for the model-governance registry. Every function is a
 * non-functional placeholder so the project links; implement them to satisfy
 * registry.h. The verifier compiles this file with an independent C harness
 * under UndefinedBehaviorSanitizer.
 */

int reg_register(const char *name, reg_metrics_t m) { (void)name; (void)m; return 0; }
int reg_version_count(const char *name) { (void)name; return 0; }
int reg_get_metrics(const char *name, int version, reg_metrics_t *out) { (void)name; (void)version; (void)out; return REG_ERR; }
int reg_set_tag(const char *name, int version, const char *key, const char *value) { (void)name; (void)version; (void)key; (void)value; return REG_ERR; }
int reg_get_tag(const char *name, int version, const char *key, char *buf, size_t buflen) { (void)name; (void)version; (void)key; (void)buf; (void)buflen; return REG_ERR; }
int reg_evaluate_gate(const char *name, int version, reg_policy_t policy) { (void)name; (void)version; (void)policy; return REG_ERR; }
int reg_set_alias(const char *name, const char *alias, int version) { (void)name; (void)alias; (void)version; return REG_ERR; }
int reg_get_alias(const char *name, const char *alias) { (void)name; (void)alias; return 0; }
int reg_promote_champion(const char *name, reg_policy_t policy) { (void)name; (void)policy; return 0; }
int reg_rollback_champion(const char *name) { (void)name; return 0; }
int reg_save(const char *path) { (void)path; return REG_ERR; }
int reg_load(const char *path) { (void)path; return REG_ERR; }
void reg_reset(void) { }
