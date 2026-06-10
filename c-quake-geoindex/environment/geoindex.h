#ifndef GEOINDEX_H
#define GEOINDEX_H

#include <stddef.h>

/*
 * Earthquake spatial-index contract.
 *
 * You implement an in-memory index of earthquake events that supports fast
 * great-circle (haversine) radius queries, removal, and Gardner-Knopoff
 * declustering. The index starts empty and grows as events are inserted; you
 * obtain and release all memory yourself with malloc/realloc/free. The harness
 * exercises the index with hundreds of thousands of events and many queries, so
 * a linear all-events scan per query is too slow — you must bucket events
 * spatially. Correctness is checked against an independent brute-force oracle and
 * your code is compiled under UndefinedBehaviorSanitizer, so out-of-bounds
 * accesses, overflow and other undefined behavior are hard errors.
 *
 * Distances use the haversine formula on a sphere of radius GI_EARTH_RADIUS_KM:
 *   d = 2*R*asin(sqrt( sin^2(dphi/2) + cos(p1)*cos(p2)*sin^2(dlmb/2) ))
 * with latitudes/longitudes converted to radians (clamp the asin argument to
 * <= 1.0). Times `t` are in days (a real number).
 */

#define GI_EARTH_RADIUS_KM 6371.0

/* Insert one event. `id` is a unique nonnegative key (the harness never inserts
 * an id that is currently live). `lat` in [-90,90], `lon` in [-180,180]. Returns
 * 0 on success, nonzero only on memory-allocation failure. */
int gi_insert(long id, double lat, double lon, double mag, double t);

/* Number of live events currently in the index. */
size_t gi_size(void);

/* Write, in ascending `id` order, the ids of every live event whose haversine
 * distance from (lat,lon) is <= radius_km (inclusive), into `out_ids` (capacity
 * `max`), and return the TRUE total number of matches. If the true count exceeds
 * `max`, write the `max` smallest ids and still return the true total. */
size_t gi_query_radius(double lat, double lon, double radius_km, long *out_ids, size_t max);

/* Remove the live event with key `id`, releasing any storage that becomes
 * unused. Returns 0 if an event was removed, nonzero if no such live event. */
int gi_remove(long id);

/* Gardner-Knopoff decluster all live events; write the surviving MAINSHOCK ids in
 * ascending `id` order into `out_ids` (capacity `max`) and return the true count
 * (writing the `max` smallest if it overflows). Each event, as a candidate
 * mainshock of magnitude M, defines a distance window L and time window T:
 *   L(M) = 10^(0.1238*M + 0.983)  km
 *   T(M) = (M >= 6.5) ? 10^(0.5409*M - 0.547) : 10^(0.032*M + 2.7389)  days
 * Process events by DECREASING magnitude, breaking ties by increasing `t`, then
 * increasing `id`. Walking that order, each event not yet removed is a mainshock
 * and removes every other not-yet-removed event `j` with haversine(i,j) <= L(M_i)
 * AND |t_j - t_i| <= T(M_i) (both inclusive, windows from the mainshock's
 * magnitude). Survivors are the events never removed. The index is unchanged by
 * this call (it is a query, not a mutation). */
size_t gi_decluster(long *out_ids, size_t max);

/* Empty the index, freeing all memory. Called between harness scenarios; after
 * it, gi_size() is 0 and the index is reusable. */
void gi_reset(void);

#endif /* GEOINDEX_H */
