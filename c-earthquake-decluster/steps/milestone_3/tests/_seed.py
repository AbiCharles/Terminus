"""Deterministic catalog seeding for the verifier.

Builds small SQLite earthquake catalogs with a known Gutenberg-Richter structure
plus injected aftershock sequences (Omori-Utsu decay, compact spatial clusters,
Gutenberg-Richter aftershock magnitudes), so each test runs the agent's `/app/quake`
against a controlled input that contains genuine space-time clusters and compares
to the independent reference (`_reference.py`). Uses only the Python standard
library; seeds are fixed so the databases are byte-stable.
"""

import datetime
import math
import random
import sqlite3

_EPOCH = datetime.datetime(2005, 1, 1)

# region: (lat_min, lat_max, lon_min, lon_max, b_true, mc_true, n_draw, depth_max)
_REGIONS = {
    "Cascadia":   (40.0, 49.0, -128.0, -122.0, 0.90, 2.0, 12000, 40.0),
    "SanAndreas": (32.0, 38.0, -123.0, -115.0, 1.00, 1.8, 14000, 25.0),
    "Aleutian":   (50.0, 58.0, -179.0, -151.0, 0.80, 2.5, 13000, 120.0),
}
_MMIN = 0.5
_SPAN_DAYS = 365.25 * 12  # 2005..2017
_KM_PER_DEG = 111.195


def _create(con):
    con.execute(
        "CREATE TABLE events ("
        "id INTEGER PRIMARY KEY, time TEXT NOT NULL, latitude REAL NOT NULL, "
        "longitude REAL NOT NULL, depth_km REAL NOT NULL, magnitude REAL NOT NULL, "
        "region TEXT NOT NULL)"
    )


def _gr(rng, b):
    return _MMIN - math.log10(1.0 - rng.random()) / b


def seed_catalog(path, seed=4242):
    """Seed a multi-region catalog with background seismicity + aftershock clusters."""
    rng = random.Random(seed)
    con = sqlite3.connect(path)
    _create(con)
    rows = []  # [datetime, lat, lon, depth, mag, region]
    for region, (la0, la1, lo0, lo1, b, mc, ndraw, dmax) in _REGIONS.items():
        for _ in range(ndraw):
            m = _gr(rng, b)
            if m > 8.0:
                continue
            pdet = 1.0 / (1.0 + math.exp(-(m - mc) / 0.20))
            if rng.random() > pdet:
                continue
            t = _EPOCH + datetime.timedelta(days=rng.uniform(0.0, _SPAN_DAYS))
            rows.append([t, rng.uniform(la0, la1), rng.uniform(lo0, lo1),
                         rng.uniform(0.5, dmax), round(m, 1), region])
    horizon = _EPOCH + datetime.timedelta(days=_SPAN_DAYS)
    for t0, la, lo, _d, mag, region in [r for r in rows if r[4] >= 4.5]:
        dwin = 10.0 ** (0.1238 * mag + 0.983)
        n_aft = int(round(8.0 * 10.0 ** (0.9 * (mag - 4.5))))
        for _ in range(n_aft):
            u = rng.random()
            dt = 0.05 * (((1.0 - u) ** (-1.0 / 0.1)) - 1.0)
            if dt > 700.0:
                continue
            at = t0 + datetime.timedelta(days=dt)
            if at > horizon:
                continue
            r_km = 0.5 * dwin * math.sqrt(rng.random())
            ang = rng.uniform(0.0, 2.0 * math.pi)
            alat = max(-89.9, min(89.9, la + (r_km * math.cos(ang)) / _KM_PER_DEG))
            alon = max(-179.9, min(179.9, lo + (r_km * math.sin(ang)) / (_KM_PER_DEG * math.cos(math.radians(la)))))
            am = _gr(rng, 1.0)
            if am > mag - 0.3:
                continue
            rows.append([at, alat, alon, rng.uniform(0.5, 35.0), round(am, 1), region])
    rows.sort(key=lambda r: (r[0], r[4]))
    out = [(t.strftime("%Y-%m-%dT%H:%M:%SZ"), round(la, 4), round(lo, 4),
            round(d, 2), m, rg) for t, la, lo, d, m, rg in rows]
    con.executemany(
        "INSERT INTO events (time, latitude, longitude, depth_km, magnitude, region) "
        "VALUES (?,?,?,?,?,?)", out)
    con.commit()
    con.close()
    return len(out)


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
