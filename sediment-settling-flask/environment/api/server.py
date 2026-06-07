"""Settling-column observations API. Serves RAW sensor readings, paginated."""
import os
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)
DB = os.environ.get("SEDIMENT_OBS_DB", "/app/api/observations.db")
PAGE_SIZE = 20


def _conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/experiments")
def experiments():
    con = _conn()
    ids = [r["experiment_id"] for r in con.execute(
        "SELECT DISTINCT experiment_id FROM observations ORDER BY experiment_id")]
    con.close()
    return jsonify(experiment_ids=ids)


@app.get("/experiments/<int:eid>/observations")
def observations(eid):
    page = request.args.get("page", default=1, type=int)
    con = _conn()
    total = con.execute(
        "SELECT COUNT(*) AS c FROM observations WHERE experiment_id = ?", (eid,)).fetchone()["c"]
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE if total else 0
    offset = (page - 1) * PAGE_SIZE
    rows = con.execute(
        "SELECT seq, t_ms, raw_level, valid FROM observations "
        "WHERE experiment_id = ? ORDER BY seq LIMIT ? OFFSET ?",
        (eid, PAGE_SIZE, offset)).fetchall()
    con.close()
    return jsonify(
        experiment_id=eid, page=page, page_size=PAGE_SIZE, total=total, total_pages=total_pages,
        observations=[dict(r) for r in rows],
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
