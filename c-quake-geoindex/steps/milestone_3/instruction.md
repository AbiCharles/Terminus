Now add **Gardner-Knopoff declustering** to the index, by extending `/app/geoindex.c`. Keep milestones 1 and 2 working; do not change `/app/geoindex.h`.

Implement `gi_decluster(out_ids, max)`: identify aftershocks/foreshocks among the live events and return the surviving **mainshocks**. Each event, considered as a candidate mainshock of magnitude `M`, defines a distance window `L(M)` km and time window `T(M)` days:

- `L(M) = 10^(0.1238*M + 0.983)`
- `T(M) = 10^(0.5409*M - 0.547)` when `M >= 6.5`, otherwise `10^(0.032*M + 2.7389)`

Process the live events in order of **decreasing magnitude**, breaking ties by **increasing `t`**, then **increasing `id`**. Walking that order, each event not yet removed is a **mainshock**, and it removes every other not-yet-removed event whose haversine distance is `<= L(M_i)` **and** whose `|t_j - t_i| <= T(M_i)` (both inclusive, windows taken from the mainshock's magnitude). The survivors are the events never removed.

Write the surviving ids in **ascending id order** into `out_ids` (capacity `max`); if the true survivor count exceeds `max`, write the `max` smallest ids but still return the true total. `gi_decluster` is a **query, not a mutation**: the index must be unchanged afterward (same `gi_size`, same contents, and calling it again returns the same answer).

The harness checks your result against an independent brute-force Gardner-Knopoff computation (including catalogs with injected aftershock clusters and catalogs that have had events removed), all under UndefinedBehaviorSanitizer, so only the exact surviving set passes. You may reuse the spatial index you built for fast neighbour lookups, but correctness — the exact processing order, the inclusive windows from the mainshock's magnitude, and leaving the index unmodified — is what is graded. Compile locally with `gcc -std=c11 -fsanitize=undefined -I/app /app/geoindex.c your_test.c` to check your work.
