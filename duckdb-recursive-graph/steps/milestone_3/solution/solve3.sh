#!/usr/bin/env bash
set -euo pipefail

# Milestone 3 oracle: sessionize each node's activations with window functions.
# A gap STRICTLY greater than 30 minutes starts a new session (a gap of exactly
# 30 minutes does not); a running sum over the new-session flags numbers the
# sessions per node (per /app/spec.md §4).
cat > /app/build_sessions.py <<'PY'
"""Create the sessions table by gaps-and-islands over activations."""
import duckdb

con = duckdb.connect("/app/graph.duckdb")
con.execute("DROP TABLE IF EXISTS sessions")
con.execute(
    """
    CREATE TABLE sessions AS
    WITH ordered AS (
        SELECT node_id, ts,
               LAG(ts) OVER (PARTITION BY node_id ORDER BY ts) AS prev_ts
        FROM activations
    ),
    flagged AS (
        SELECT node_id, ts,
               CASE WHEN prev_ts IS NULL OR ts - prev_ts > INTERVAL 30 MINUTE
                    THEN 1 ELSE 0 END AS is_new
        FROM ordered
    ),
    numbered AS (
        SELECT node_id, ts,
               SUM(is_new) OVER (PARTITION BY node_id ORDER BY ts
                                 ROWS UNBOUNDED PRECEDING) AS session_index
        FROM flagged
    )
    SELECT node_id, session_index,
           MIN(ts) AS start_ts, MAX(ts) AS end_ts, COUNT(*) AS num_events
    FROM numbered
    GROUP BY node_id, session_index
    """
)
n = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
con.close()
print(f"sessions: {n}")
PY

python3 /app/build_sessions.py
