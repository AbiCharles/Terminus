#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: build the discrete-time person-period table with SQL.
# Each subject is expanded into one row per period 1..time_observed via a
# correlated generate_series, with event_in_period flagged only in the subject's
# event period (per /app/spec.md §3).
cat > /app/build_person_period.py <<'PY'
"""Create the person_period table from subjects via discrete-time expansion."""
import duckdb

con = duckdb.connect("/app/survival.duckdb")
con.execute("DROP TABLE IF EXISTS person_period")
con.execute(
    """
    CREATE TABLE person_period AS
    SELECT s.subject_id,
           CAST(p.period AS INTEGER)            AS period,
           s.age, s.biomarker, s.treatment, s.stage, s.sex, s.split,
           CASE WHEN s.event = 1 AND p.period = s.time_observed THEN 1 ELSE 0 END
                                                AS event_in_period
    FROM subjects s, generate_series(1, s.time_observed) AS p(period)
    """
)
n = con.execute("SELECT COUNT(*) FROM person_period").fetchone()[0]
expected = con.execute("SELECT SUM(time_observed) FROM subjects").fetchone()[0]
con.close()
print(f"person_period rows: {n} (expected {expected})")
PY

python3 /app/build_person_period.py
