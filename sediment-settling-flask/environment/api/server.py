"""Settling-column observation API.

Serves RAW sensor readings (ADC counts) for each experiment, paginated. Clients
must convert raw readings to physical height using the per-sensor calibration in
experiments.db (height_cm = raw_level * raw_scale + raw_offset) and time via
t_s = t_ms / 1000.
"""
import os
import sqlite3

from flask import Flask, abort, jsonify, request

OBS_DB = os.environ.get("OBS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "observations.db"))
PAGE_SIZE = 25

app = Flask(__name__)


def _conn():
    return sqlite3.connect(OBS_DB)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/experiments")
def experiments():
    con = _conn()
    ids = [r[0] for r in con.execute(
        "SELECT DISTINCT experiment_id FROM observations ORDER BY experiment_id"
    )]
    con.close()
    return jsonify(experiment_ids=ids)


@app.get("/experiments/<int:experiment_id>/observations")
def observations(experiment_id):
    page = request.args.get("page", default=1, type=int)
    if page is None or page < 1:
        abort(400, description="page must be a positive integer")
    con = _conn()
    total = con.execute(
        "SELECT COUNT(*) FROM observations WHERE experiment_id = ?", (experiment_id,)
    ).fetchone()[0]
    if total == 0:
        con.close()
        abort(404, description="unknown experiment_id")
    offset = (page - 1) * PAGE_SIZE
    rows = con.execute(
        "SELECT t_ms, raw_level FROM observations WHERE experiment_id = ? "
        "ORDER BY seq LIMIT ? OFFSET ?",
        (experiment_id, PAGE_SIZE, offset),
    ).fetchall()
    con.close()
    n_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    return jsonify(
        experiment_id=experiment_id,
        page=page,
        page_size=PAGE_SIZE,
        total=total,
        next=(page + 1 if page < n_pages else None),
        observations=[{"t_ms": t_ms, "raw_level": raw_level} for t_ms, raw_level in rows],
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
