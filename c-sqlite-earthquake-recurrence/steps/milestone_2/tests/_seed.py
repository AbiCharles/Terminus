"""Deterministic catalog seeding for the verifier.

Builds small SQLite earthquake catalogs with a known Gutenberg-Richter structure
so each test runs the agent's compiled `/app/quake` against a controlled input
and compares to the independent reference (`_reference.py`). Uses only the Python
standard library; seeds are fixed so the databases are byte-stable.
"""

import datetime
import math
import random
import sqlite3

_EPOCH = datetime.datetime(2005, 1, 1)

# region: (lat_min, lat_max, lon_min, lon_max, b_true, mc_true, n_draw, depth_max)
_REGIONS = {
    "Cascadia":   (40.0, 49.0, -128.0, -122.0, 0.90, 2.0, 30000, 40.0),
    "SanAndreas": (32.0, 38.0, -123.0, -115.0, 1.00, 1.8, 36000, 25.0),
    "Aleutian":   (50.0, 58.0, -180.0, -150.0, 0.80, 2.5, 34000, 120.0),
}
_MMIN = 0.5
_SPAN_DAYS = 365.25 * 12  # 2005..2017


def _create(con):
    con.execute(
        "CREATE TABLE events ("
        "id INTEGER PRIMARY KEY, time TEXT NOT NULL, latitude REAL NOT NULL, "
        "longitude REAL NOT NULL, depth_km REAL NOT NULL, magnitude REAL NOT NULL, "
        "region TEXT NOT NULL)"
    )


def seed_catalog(path, seed=4242):
    """Seed a realistic multi-region catalog (a few thousand events)."""
    rng = random.Random(seed)
    con = sqlite3.connect(path)
    _create(con)
    rows = []
    for region, (la0, la1, lo0, lo1, b, mc, ndraw, dmax) in _REGIONS.items():
        for _ in range(ndraw):
            u = rng.random()
            m = _MMIN - math.log10(1.0 - u) / b
            if m > 8.0:
                continue
            pdet = 1.0 / (1.0 + math.exp(-(m - mc) / 0.20))
            if rng.random() > pdet:
                continue
            m = round(m, 1)
            t = (_EPOCH + datetime.timedelta(days=rng.uniform(0.0, _SPAN_DAYS))).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            rows.append((t, round(rng.uniform(la0, la1), 4), round(rng.uniform(lo0, lo1), 4),
                         round(rng.uniform(0.5, dmax), 2), m, region))
    rows.sort(key=lambda r: r[0])
    con.executemany(
        "INSERT INTO events (time, latitude, longitude, depth_km, magnitude, region) "
        "VALUES (?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return len(rows)


def seed_tiny(path):
    """Seed a catalog too small for completeness estimation (for exit-code 3)."""
    con = sqlite3.connect(path)
    _create(con)
    rows = []
    for i in range(10):
        m = round(1.0 + 0.1 * i, 1)
        t = (_EPOCH + datetime.timedelta(days=10 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append((t, 41.0, -124.0, 5.0, m, "Cascadia"))
    con.executemany(
        "INSERT INTO events (time, latitude, longitude, depth_km, magnitude, region) "
        "VALUES (?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return len(rows)
