#!/usr/bin/env bash
set -euo pipefail

# Milestone 1 oracle: build the discrete-time person-period table with SQL. Each
# subject is expanded to one row per period 1..time_observed; the time-varying
# biomarker is attached by LOCF (an ASOF join over the materialized skeleton,
# since a correlated generate_series cannot be combined with an ASOF join), and
# the 3-class competing-risks period_outcome is flagged (per /app/spec.md §3).
cat > /app/build_person_period.py <<'PY'
"""Create the person_period table: discrete-time expansion + LOCF biomarker."""
import duckdb

con = duckdb.connect("/app/survival.duckdb")
con.execute("DROP TABLE IF EXISTS person_period")
con.execute(
    """
    CREATE TABLE person_period AS
    WITH skeleton AS (
        SELECT s.subject_id, CAST(p.period AS INTEGER) AS period,
               s.age, s.treatment, s.stage, s.sex, s.split,
               s.time_observed, s.event_type
        FROM subjects s, generate_series(1, s.time_observed) AS p(period)
    )
    SELECT k.subject_id, k.period, k.age, m.biomarker, k.treatment, k.stage,
           k.sex, k.split,
           CASE WHEN k.event_type = 1 AND k.period = k.time_observed THEN 1
                WHEN k.event_type = 2 AND k.period = k.time_observed THEN 2
                ELSE 0 END AS period_outcome
    FROM skeleton k
    ASOF LEFT JOIN measurements m
      ON m.subject_id = k.subject_id AND m.period <= k.period
    """
)
n = con.execute("SELECT COUNT(*) FROM person_period").fetchone()[0]
expected = con.execute("SELECT SUM(time_observed) FROM subjects").fetchone()[0]
nulls = con.execute("SELECT COUNT(*) FROM person_period WHERE biomarker IS NULL").fetchone()[0]
con.close()
print(f"person_period rows: {n} (expected {expected}); null biomarker: {nulls}")
PY

python3 /app/build_person_period.py
