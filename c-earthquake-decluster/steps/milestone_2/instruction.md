Add a `decluster` subcommand: `/app/quake decluster [filters] --out PATH`. It accepts the same filters as `query`, removes aftershocks and foreshocks from the filtered events with the Gardner & Knopoff (1974) windowing method, and writes the surviving **mainshock** events as CSV to `PATH`, in the same format as `query`.

Declustering identifies space-time clusters and keeps only the largest event of each cluster. Implement it exactly as follows; the result must be reproducible to the event, so every rule below is mandatory.

Each event, when considered as a potential mainshock, defines a distance window `L` (in kilometres) and a time window `T` (in days) from its own magnitude `M`:

- `L(M) = 10^(0.1238 * M + 0.983)`
- `T(M) = 10^(0.5409 * M - 0.547)` when `M >= 6.5`, otherwise `T(M) = 10^(0.032 * M + 2.7389)`

The great-circle distance between two events is the haversine distance on a sphere of radius `R = 6371.0` km: with latitudes/longitudes converted to radians, `d = 2 * R * asin( sqrt( sin^2(Δφ/2) + cos(φ1) * cos(φ2) * sin^2(Δλ/2) ) )`, where `Δφ` and `Δλ` are the latitude and longitude differences. Clamp the argument of `asin` to at most `1.0` before taking the square root's arcsine. The time separation between two events is the absolute difference of their Julian days, where each event's Julian day is computed from its **full ISO-8601 `time` value including the time-of-day** — equivalently `julianday(time)` using SQLite's `julianday()` applied to the complete `YYYY-MM-DDTHH:MM:SSZ` timestamp, not just the date portion.

Process the filtered events as follows:

1. Order the events by **decreasing magnitude**; break ties by **increasing time** (compare the Julian days), and break remaining ties by **increasing `id`**. This is the order in which events are considered as mainshocks.
2. Mark every event as not-yet-removed. Walk the events in the order from step 1. If the current event is already marked removed, skip it. Otherwise the current event `i` is a **mainshock**: for every other event `j` (`j != i`) that is not yet marked removed, mark `j` as removed when **both** `haversine(i, j) <= L(M_i)` **and** `|julianday(time_j) - julianday(time_i)| <= T(M_i)` hold. Both windows are taken from the mainshock `i`'s magnitude `M_i`, both bounds are inclusive, and a `j` removed by one mainshock can never itself become a mainshock.
3. The declustered catalog is exactly the set of events that were never marked removed.

Write the surviving mainshocks as CSV with the exact `query` header `id,time,latitude,longitude,depth_km,magnitude,region`, one row per mainshock ordered by `time` ascending and then `id` ascending, using the same deterministic numeric formatting as `query` (`latitude`/`longitude` four decimals, `depth_km` two, `magnitude` one; `id`, `time`, `region` verbatim). A valid filter that matches no events writes the header row alone and exits `0`.

Exit with status code `2` for any invalid invocation — exactly the cases listed for `query` (unknown flag, missing flag value, non-numeric value where a number is required, a min greater than its corresponding max, a latitude outside [-90, 90] or longitude outside [-180, 180]). Validate the arguments before running any declustering. On success exit `0`.
