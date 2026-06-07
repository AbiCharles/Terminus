"""Independent reference for the earthquake recurrence analyzer.

Recomputes, directly from a SQLite catalog and using only the Python standard
library, the canonical answers the agent's C tool must produce: the filtered
event set, the Wiemer & Wyss (2000) goodness-of-fit magnitude of completeness,
the Aki-Utsu b-value with Shi & Bolt (1982) uncertainty, the a-value, and
Poisson exceedance probabilities. It never reads the agent's output files, so an
agent cannot weaken verification by tampering with its own results, and the C
solution has no access to this module. The numerical conventions here (delta_m
binning, the 90% GFT confidence target, the MIN_SAMPLE / MIN_BINS thresholds)
are the binding definitions of the task's deterministic outputs.
"""

import math
import sqlite3

DELTA_M = 0.1
GFT_CONFIDENCE = 90.0
MIN_SAMPLE = 30
MIN_BINS_ABOVE_MC = 4

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


def _aggregate(db_path, filters):
    con = sqlite3.connect(db_path)
    try:
        where, params = _where(filters)
        n, mmin, mmax, years = con.execute(
            "SELECT COUNT(*), MIN(magnitude), MAX(magnitude),"
            " (julianday(MAX(time)) - julianday(MIN(time)))/365.25 FROM events" + where,
            params,
        ).fetchone()
        mags = [r[0] for r in con.execute(
            "SELECT magnitude FROM events" + where + " ORDER BY magnitude ASC", params)]
    finally:
        con.close()
    return n, mmin, mmax, years, mags


def _bin(m):
    return math.floor(m / DELTA_M + 0.5)


def aki_b(mags, mc):
    mean = sum(mags) / len(mags)
    denom = mean - (mc - DELTA_M / 2.0)
    if denom <= 0:
        return None, mean
    return math.log10(math.e) / denom, mean


def gft_mc(mags):
    """Lowest candidate Mc reaching the 90% GFT residual, else the best-fit Mc.
    Returns (mc, R) or None when no fit is possible."""
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


def compute_stats(db_path, filters):
    """Full statistics dict, or raises ValueError for an insufficient sample."""
    n, mmin, mmax, years, mags = _aggregate(db_path, filters)
    if n == 0:
        raise ValueError("no events match the filters")
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
        "catalog_years": years,
        "magnitude_range": {"min": mmin, "max": mmax},
        "gft_R": R,
    }


def fmd(db_path, filters):
    """Non-cumulative + cumulative frequency-magnitude distribution rows."""
    _n, _mmin, _mmax, _years, mags = _aggregate(db_path, filters)
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
