#include "geoindex.h"

/*
 * Starting stub for the earthquake spatial index. Every function is a
 * non-functional placeholder so the project links; implement them to satisfy
 * geoindex.h. The verifier compiles this file together with an independent C
 * harness under UndefinedBehaviorSanitizer.
 */

int gi_insert(long id, double lat, double lon, double mag, double t) {
    (void)id; (void)lat; (void)lon; (void)mag; (void)t;
    return 0;
}

size_t gi_size(void) {
    return 0;
}

size_t gi_query_radius(double lat, double lon, double radius_km, long *out_ids, size_t max) {
    (void)lat; (void)lon; (void)radius_km; (void)out_ids; (void)max;
    return 0;
}

int gi_remove(long id) {
    (void)id;
    return 1;
}

size_t gi_decluster(long *out_ids, size_t max) {
    (void)out_ids; (void)max;
    return 0;
}

void gi_reset(void) {
}
