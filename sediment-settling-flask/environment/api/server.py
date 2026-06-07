"""Settling-column observation API.

The timing and level streams are served by SEPARATE paginated endpoints and must
be joined on `seq` to reconstruct each observation:

  GET /experiments/<id>/timestamps  -> {seq, t_ms} ordered by seq
  GET /experiments/<id>/levels      -> {seq, raw_level} returned in the sensor's
                                       acquisition order (NOT sorted by seq)

Raw levels are converted to physical height with the per-sensor calibration in
experiments.db (height_cm = raw_level * raw_scale + raw_offset); time_s = t_ms/1000.
"""
import os
import sqlite3

from flask import Flask, abort, jsonify, request

OBS_DB = os.environ.get("OBS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "observations.db"))
PAGE_SIZE = 25

app = Flask(__name__)


def _conn():
    return sqlite3.connect(OBS_DB)


def _page(table, value_cols, key):
    experiment_id = int(request.view_args["experiment_id"])
    page = request.args.get("page", default=1, type=int)
    if page is None or page < 1:
        abort(400, description="page must be a positive integer")
    con = _conn()
    total = con.execute(
        f"SELECT COUNT(*) FROM {table} WHERE experiment_id = ?", (experiment_id,)
    ).fetchone()[0]
    if total == 0:
        con.close()
        abort(404, description="unknown experiment_id")
    offset = (page - 1) * PAGE_SIZE
    cols = ", ".join(value_cols)
    rows = con.execute(
        f"SELECT {cols} FROM {table} WHERE experiment_id = ? ORDER BY ord_idx LIMIT ? OFFSET ?",
        (experiment_id, PAGE_SIZE, offset),
    ).fetchall()
    con.close()
    n_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    return jsonify(
        experiment_id=experiment_id, page=page, page_size=PAGE_SIZE, total=total,
        next=(page + 1 if page < n_pages else None),
        **{key: [dict(zip(value_cols, r)) for r in rows]},
    )


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/experiments")
def experiments():
    con = _conn()
    ids = [r[0] for r in con.execute(
        "SELECT DISTINCT experiment_id FROM timestamps ORDER BY experiment_id")]
    con.close()
    return jsonify(experiment_ids=ids)


@app.get("/experiments/<int:experiment_id>/timestamps")
def timestamps(experiment_id):
    return _page("timestamps", ["seq", "t_ms"], "timestamps")


@app.get("/experiments/<int:experiment_id>/levels")
def levels(experiment_id):
    return _page("levels", ["seq", "raw_level"], "levels")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
