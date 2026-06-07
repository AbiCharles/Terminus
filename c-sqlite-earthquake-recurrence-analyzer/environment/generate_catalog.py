"""Build the seeded SQLite earthquake catalog shipped to the agent at
/app/catalog.db.

Run at image-build time only (in a throwaway builder stage); the agent never sees
this script. Each tectonic region is populated with a Gutenberg-Richter
magnitude distribution (region-specific b-value and true completeness) thinned by
a logistic detection roll-off below completeness, plus seeded times, locations
and depths, so the catalog is realistic and fully deterministic. Uses only the
Python standard library.
"""

import datetime
import math
import random
import sqlite3
import sys

# region: (lat_min, lat_max, lon_min, lon_max, b_true, mc_true, n_draw, depth_max)
REGIONS = {
    "Cascadia":    (40.0, 49.0, -128.0, -122.0, 0.90, 2.0, 60000, 40.0),
    "SanAndreas":  (32.0, 38.0, -123.0, -115.0, 1.00, 1.8, 80000, 25.0),
    "Aleutian":    (50.0, 58.0, -180.0, -150.0, 0.80, 2.5, 70000, 120.0),
    "Hawaii":      (18.0, 22.0, -157.0, -154.0, 1.10, 1.5, 50000, 60.0),
}

MMIN = 0.5
EPOCH = datetime.datetime(2000, 1, 1)
SPAN_DAYS = 365.25 * 20  # 2000..2020


def synthesize(con):
    rng = random.Random(20240601)
    rows = []
    eid = 0
    for region, (la0, la1, lo0, lo1, b, mc, ndraw, dmax) in REGIONS.items():
        for _ in range(ndraw):
            u = rng.random()
            m = MMIN - math.log10(1.0 - u) / b
            if m > 8.0:
                continue
            # logistic detection probability, ~0.5 at mc_true
            pdet = 1.0 / (1.0 + math.exp(-(m - mc) / 0.20))
            if rng.random() > pdet:
                continue
            m = round(m, 1)
            eid += 1
            t = (EPOCH + datetime.timedelta(days=rng.uniform(0.0, SPAN_DAYS))).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            lat = round(rng.uniform(la0, la1), 4)
            lon = round(rng.uniform(lo0, lo1), 4)
            depth = round(rng.uniform(0.5, dmax), 2)
            rows.append((eid, t, lat, lon, depth, m, region))
    rows.sort(key=lambda r: (r[1], r[0]))
    # reassign ids in time order for a tidy catalog
    rows = [(i + 1, t, la, lo, d, m, rg) for i, (_, t, la, lo, d, m, rg) in enumerate(rows)]
    con.executemany("INSERT INTO events VALUES (?,?,?,?,?,?,?)", rows)
    return len(rows)


def main(db_path):
    con = sqlite3.connect(db_path)
    con.execute(
        "CREATE TABLE events ("
        "id INTEGER PRIMARY KEY, time TEXT NOT NULL, latitude REAL NOT NULL, "
        "longitude REAL NOT NULL, depth_km REAL NOT NULL, magnitude REAL NOT NULL, "
        "region TEXT NOT NULL)"
    )
    n = synthesize(con)
    con.execute("CREATE INDEX idx_events_region ON events(region)")
    con.execute("CREATE INDEX idx_events_time ON events(time)")
    con.commit()
    con.close()
    print(f"seeded {n} events")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "catalog.db")
