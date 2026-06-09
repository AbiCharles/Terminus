"""Build the seeded SQLite earthquake catalog shipped to the agent at
/app/catalog.db.

Run at image-build time only (in a throwaway builder stage); the agent never sees
this script. Each tectonic region is populated with a Gutenberg-Richter
magnitude distribution (region-specific b-value and true completeness) thinned by
a logistic detection roll-off below completeness. On top of that background
seismicity, aftershock sequences are injected around the larger events
(Omori-Utsu temporal decay, compact spatial clustering, Gutenberg-Richter
aftershock magnitudes), so the catalog contains genuine space-time clusters that
a Gardner-Knopoff declustering pass must identify and remove. Everything is
seeded and uses only the Python standard library, so the catalog is fully
deterministic.
"""

import datetime
import math
import random
import sqlite3
import sys

# region: (lat_min, lat_max, lon_min, lon_max, b_true, mc_true, n_draw, depth_max)
REGIONS = {
    "Cascadia":   (40.0, 49.0, -127.0, -123.0, 0.90, 2.0, 12000, 40.0),
    "SanAndreas": (32.0, 38.0, -122.0, -116.0, 1.00, 1.8, 16000, 25.0),
    "Aleutian":   (51.0, 57.0, -178.0, -152.0, 0.80, 2.5, 13000, 120.0),
    "Hawaii":     (18.5, 21.5, -156.5, -154.5, 1.10, 1.5, 9000, 60.0),
}

MMIN = 0.5
EPOCH = datetime.datetime(2000, 1, 1)
SPAN_DAYS = 365.25 * 20  # 2000..2020
KM_PER_DEG = 111.195  # mean km per degree of latitude


def _gr_magnitude(rng, b):
    """Draw a Gutenberg-Richter magnitude (>= MMIN) with slope b."""
    return MMIN - math.log10(1.0 - rng.random()) / b


def synthesize(con):
    rng = random.Random(20240601)
    rows = []  # mutable [datetime, lat, lon, depth, mag, region]

    # 1. Background seismicity: independent Gutenberg-Richter events per region,
    #    thinned by a logistic detection probability centred on the region's mc.
    for region, (la0, la1, lo0, lo1, b, mc, ndraw, dmax) in REGIONS.items():
        for _ in range(ndraw):
            m = _gr_magnitude(rng, b)
            if m > 8.0:
                continue
            pdet = 1.0 / (1.0 + math.exp(-(m - mc) / 0.20))
            if rng.random() > pdet:
                continue
            t = EPOCH + datetime.timedelta(days=rng.uniform(0.0, SPAN_DAYS))
            lat = rng.uniform(la0, la1)
            lon = rng.uniform(lo0, lo1)
            depth = rng.uniform(0.5, dmax)
            rows.append([t, lat, lon, depth, round(m, 1), region])

    # 2. Aftershock sequences: every background event with magnitude >= 5.0 seeds a
    #    cluster. Aftershock count grows with mainshock magnitude (Utsu productivity),
    #    times follow modified-Omori decay, locations are compact around the
    #    mainshock, and magnitudes are Gutenberg-Richter capped below the mainshock
    #    (Bath's law). These land well inside the Gardner-Knopoff windows, so a
    #    correct declustering removes them.
    horizon = EPOCH + datetime.timedelta(days=SPAN_DAYS)
    mainshocks = [r for r in rows if r[4] >= 5.0]
    for t0, la, lo, _depth, mag, region in mainshocks:
        dwin_km = 10.0 ** (0.1238 * mag + 0.983)
        n_aft = int(round(8.0 * 10.0 ** (0.9 * (mag - 5.0))))
        for _ in range(n_aft):
            # modified-Omori elapsed days (p=1.1, c=0.05), kept inside the window
            u = rng.random()
            dt_days = 0.05 * (((1.0 - u) ** (-1.0 / 0.1)) - 1.0)
            if dt_days > 700.0:
                continue
            at = t0 + datetime.timedelta(days=dt_days)
            if at > horizon:
                continue
            # compact spatial cluster within half the distance window
            r_km = 0.5 * dwin_km * math.sqrt(rng.random())
            ang = rng.uniform(0.0, 2.0 * math.pi)
            alat = la + (r_km * math.cos(ang)) / KM_PER_DEG
            alon = lo + (r_km * math.sin(ang)) / (KM_PER_DEG * math.cos(math.radians(la)))
            alat = max(-89.9, min(89.9, alat))
            alon = max(-179.9, min(179.9, alon))
            am = _gr_magnitude(rng, 1.0)
            if am > mag - 0.3:
                continue
            depth = rng.uniform(0.5, 35.0)
            rows.append([at, alat, alon, depth, round(am, 1), region])

    # 3. Finalise: order by time then magnitude, assign ids in that order.
    rows.sort(key=lambda r: (r[0], r[4]))
    out = [
        (
            i + 1,
            t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            round(lat, 4),
            round(lon, 4),
            round(depth, 2),
            round(mag, 1),
            region,
        )
        for i, (t, lat, lon, depth, mag, region) in enumerate(rows)
    ]
    con.executemany("INSERT INTO events VALUES (?,?,?,?,?,?,?)", out)
    return len(out)


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
