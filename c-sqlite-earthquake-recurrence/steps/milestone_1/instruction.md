Build a C command-line tool, compiled to `/app/quake`, that analyzes the earthquake catalog in the SQLite database at `/app/catalog.db`. The catalog has one table, `events(id INTEGER, time TEXT, latitude REAL, longitude REAL, depth_km REAL, magnitude REAL, region TEXT)`, where `time` is an ISO-8601 UTC string like `2014-07-02T11:23:05Z`. Compile against the system SQLite library (`-lsqlite3`) and read the catalog only through SQL queries — do not parse the database file yourself.

This milestone implements the `query` subcommand: `/app/quake query [filters] --out PATH`. It selects the matching events and writes them as CSV to `PATH`. Support these filters, all optional and combinable (a filter that is omitted imposes no constraint); every constraint must be applied in SQL, not in C after the fact:

- `--region NAME` — exact match on the `region` column.
- `--lat-min V`, `--lat-max V`, `--lon-min V`, `--lon-max V` — inclusive bounding box on `latitude`/`longitude`.
- `--start ISO`, `--end ISO` — inclusive bounds on `time` (string comparison on the ISO timestamps).
- `--depth-min V`, `--depth-max V` — inclusive bounds on `depth_km`.
- `--mag-min V`, `--mag-max V` — inclusive bounds on `magnitude`.
- `--db PATH` — catalog path, defaulting to `/app/catalog.db`.

A named region and a bounding box may be supplied together; when both are present an event must satisfy both. The CSV must have the exact header `id,time,latitude,longitude,depth_km,magnitude,region` followed by one row per matching event ordered by `time` ascending and then `id` ascending. Format the numeric columns deterministically: `latitude` and `longitude` with four digits after the decimal point, `depth_km` with two, and `magnitude` with one; write `id`, `time` and `region` verbatim.

Exit with status code `2` for any invalid invocation — an unknown flag, a missing flag value, a non-numeric value where a number is required, a min greater than its corresponding max (latitude, longitude, depth, magnitude, or start after end), or a latitude outside [-90, 90] or longitude outside [-180, 180]. On success exit `0`. A valid filter that simply matches no events is not an error: write the header row alone and exit `0`.
