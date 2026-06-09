"""Independent reference for the earthquake declustering + recurrence analyzer.

Recomputes, directly from a SQLite catalog and using only the Python standard
library, the canonical answers the agent's tool must produce: the filtered event
set (milestone 1), the Gardner & Knopoff (1974) declustered mainshock catalog
(milestone 2), and the Wiemer & Wyss (2000) goodness-of-fit completeness, the
Aki-Utsu b-value with Shi & Bolt (1982) uncertainty, the a-value and Poisson
exceedance probabilities computed **on the declustered catalog** (milestone 3).
It never reads the agent's output files, so an agent cannot weaken verification
by tampering with its own results, and the agent solution has no access to this
module. The numerical conventions here are the binding definitions of the task's
deterministic outputs.
"""

import math
import sqlite3

DELTA_M = 0.1
GFT_CONFIDENCE = 90.0
MIN_SAMPLE = 30
MIN_BINS_ABOVE_MC = 4
EARTH_RADIUS_KM = 6371.0

COLUMNS = ("id", "time", "latitude", "longitude", "depth_km", "magnitude", "region")


def _where(filters):
    """Build a parameterized WHERE clause + params from a filter dict."""
    clauses = ["1=1"]
    params = []
    if filters.get("region") is not None:
        clauses.append("region = ?")
        params.append(filters["region"])
    for col, key, op in (
        ("latitude", "lat_min", ">="), ("latitude", "lat_max", "<="),
        ("longitude", "lon_min", ">="), ("longitude", "lon_max", "<="),
        ("time", "start", ">="), ("time", "end", "<="),
        ("depth_km", "depth_min", ">="), ("depth_km", "depth_max", "<="),
        ("magnitude", "mag_min", ">="), ("magnitude", "mag_max", "<="),
    ):
        if filters.get(key) is not None:
            clauses.append(f"{col} {op} ?")
            params.append(filters[key])
    return " WHERE " + " AND ".join(clauses), params


def query_events(db_path, filters):
    """Return filtered rows as dicts, ordered by (time, id) — mirrors `query`."""
    con = sqlite3.connect(db_path)
    try:
        where, params = _where(filters)
        sql = ("SELECT id, time, latitude, longitude, depth_km, magnitude, region "
               "FROM events" + where + " ORDER BY time ASC, id ASC")
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    return [dict(zip(COLUMNS, r)) for r in rows]


# --------------------------------------------------------------------------- #
# Milestone 2: Gardner-Knopoff declustering                                   #
# --------------------------------------------------------------------------- #

def _gk_windows(M):
    """Distance window (km) and time window (days) from a mainshock magnitude."""
    L = 10.0 ** (0.1238 * M + 0.983)
    if M >= 6.5:
        T = 10.0 ** (0.5409 * M - 0.547)
    else:
        T = 10.0 ** (0.032 * M + 2.7389)
    return L, T


def _haversine_km(la1, lo1, la2, lo2):
    p1 = math.radians(la1)
    p2 = math.radians(la2)
    dphi = math.radians(la2 - la1)
    dlmb = math.radians(lo2 - lo1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2.0) ** 2
    a = min(1.0, a)
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _julianday(con, ts):
    return con.execute("SELECT julianday(?)", (ts,)).fetchone()[0]


def decluster(db_path, filters):
    """Gardner-Knopoff declustered mainshocks, ordered by (time, id).

    Process events by decreasing magnitude (ties: increasing julianday, then
    increasing id); each not-yet-removed event is a mainshock that removes every
    other not-yet-removed event within its magnitude-defined haversine distance
    window and absolute julianday time window (inclusive). Survivors are the
    mainshocks.
    """
    events = query_events(db_path, filters)  # (time, id) order
    n = len(events)
    if n == 0:
        return []
    con = sqlite3.connect(db_path)
    try:
        jcache = {}
        for e in events:
            ts = e["time"]
            if ts not in jcache:
                jcache[ts] = _julianday(con, ts)
            e["_jd"] = jcache[ts]
    finally:
        con.close()
    order = sorted(range(n), key=lambda i: (-events[i]["magnitude"], events[i]["_jd"], events[i]["id"]))
    removed = [False] * n
    for i in order:
        if removed[i]:
            continue
        ei = events[i]
        L, T = _gk_windows(ei["magnitude"])
        for j in range(n):
            if j == i or removed[j]:
                continue
            ej = events[j]
            if abs(ej["_jd"] - ei["_jd"]) <= T and _haversine_km(
                ei["latitude"], ei["longitude"], ej["latitude"], ej["longitude"]
            ) <= L:
                removed[j] = True
    mains = [events[i] for i in range(n) if not removed[i]]  # preserves (time, id) order
    for e in mains:
        e.pop("_jd", None)
    return mains


# --------------------------------------------------------------------------- #
# Milestone 3: recurrence statistics on the DECLUSTERED catalog               #
# --------------------------------------------------------------------------- #

def _bin(m):
    return math.floor(m / DELTA_M + 0.5)


def aki_b(mags, mc):
    mean = sum(mags) / len(mags)
    denom = mean - (mc - DELTA_M / 2.0)
    if denom <= 0:
        return None, mean
    return math.log10(math.e) / denom, mean


def gft_mc(mags):
    """Lowest candidate Mc reaching the 90% GFT residual, else the best-fit Mc."""
    if not mags:
        return None
    bins = [_bin(m) for m in mags]
    bmin, bmax = min(bins), max(bins)
    nbins = bmax - bmin + 1
    if nbins < MIN_BINS_ABOVE_MC:
        return None
    hist = [0] * nbins
    for b in bins:
        hist[b - bmin] += 1
    best_R, best_mc = -1e9, None
    for c in range(0, nbins - (MIN_BINS_ABOVE_MC - 1)):
        mc = (bmin + c) * DELTA_M
        sample = [m for m in mags if _bin(m) >= bmin + c]
        if len(sample) < MIN_SAMPLE:
            continue
        mean = sum(sample) / len(sample)
        denom = mean - (mc - DELTA_M / 2.0)
        if denom <= 0:
            continue
        b = math.log10(math.e) / denom
        a = math.log10(len(sample)) + b * mc
        abs_sum = obs_sum = 0.0
        for k in range(c, nbins):
            center = (bmin + k) * DELTA_M
            obs_cum = sum(hist[k:])
            pred_cum = 10.0 ** (a - b * center)
            abs_sum += abs(obs_cum - pred_cum)
            obs_sum += obs_cum
        R = 100.0 * (1.0 - abs_sum / obs_sum)
        if R > best_R:
            best_R, best_mc = R, mc
        if R >= GFT_CONFIDENCE:
            return mc, R
    if best_mc is not None:
        return best_mc, best_R
    return None


def _catalog_years(events):
    if not events:
        return 0.0
    times = [e["time"] for e in events]
    con = sqlite3.connect(":memory:")
    try:
        jmin = _julianday(con, min(times))
        jmax = _julianday(con, max(times))
    finally:
        con.close()
    return (jmax - jmin) / 365.25


def compute_stats(db_path, filters):
    """Statistics on the DECLUSTERED catalog, or ValueError for an insufficient sample."""
    events = decluster(db_path, filters)
    n = len(events)
    if n == 0:
        raise ValueError("no events match the filters")
    mags = sorted(e["magnitude"] for e in events)
    res = gft_mc(mags)
    if res is None:
        raise ValueError("insufficient sample for completeness estimation")
    mc, R = res
    cmin = _bin(mc)
    above = [m for m in mags if _bin(m) >= cmin]
    if len(above) < MIN_SAMPLE:
        raise ValueError(f"only {len(above)} events at/above Mc")
    b, mean = aki_b(above, mc)
    if b is None or b <= 0:
        raise ValueError("degenerate magnitude distribution")
    var = sum((m - mean) ** 2 for m in above) / (len(above) * (len(above) - 1))
    sigma_b = 2.30 * b * b * math.sqrt(var)
    a = math.log10(len(above)) + b * mc
    return {
        "n_total": n,
        "n_above_mc": len(above),
        "mc": mc,
        "b_value": b,
        "b_uncertainty": sigma_b,
        "a_value": a,
        "catalog_years": _catalog_years(events),
        "magnitude_range": {"min": min(mags), "max": max(mags)},
        "gft_R": R,
    }


def fmd(db_path, filters):
    """Non-cumulative + cumulative FMD rows on the DECLUSTERED catalog."""
    events = decluster(db_path, filters)
    mags = [e["magnitude"] for e in events]
    bins = [_bin(m) for m in mags]
    bmin, bmax = min(bins), max(bins)
    nbins = bmax - bmin + 1
    hist = [0] * nbins
    for b in bins:
        hist[b - bmin] += 1
    out = []
    for k in range(nbins):
        out.append((round((bmin + k) * DELTA_M, 1), hist[k], sum(hist[k:])))
    return out


def exceedance(stats, targets, window_years):
    """Poisson exceedance probabilities from the G-R fit."""
    out = []
    for M in targets:
        expected_count = 10.0 ** (stats["a_value"] - stats["b_value"] * M)
        annual_rate = expected_count / stats["catalog_years"]
        prob = 1.0 - math.exp(-annual_rate * window_years)
        out.append({"magnitude": M, "annual_rate": annual_rate, "exceedance_probability": prob})
    return out
