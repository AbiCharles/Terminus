We're building a command-line tool that analyses computational-fluid-dynamics (CFD) snapshot data served by a small Ruby on Rails API. You'll build it over three milestones in `/app/pod_cli.rb` — a non-functional stub is already there for you to replace. Use only the Ruby standard library (`net/http`, `json`, etc.). Do NOT use linear-algebra libraries: no `numo`, no `nmatrix`, and not Ruby's `Matrix` eigensolver — you implement the numerics from scratch.

The Rails API is already running at `http://localhost:8000` (it auto-starts; if needed, `/opt/start_api.sh` is idempotent). Its source is at `/opt/api` and you may read it. Endpoints:

- `GET /experiments` → `{ "experiments": [ { "id", "is_fixture", "n_dofs", "n_frames", "n_pages" }, ... ] }`
- `GET /experiments/<id>` → metadata `{ "id", "field", "n_dofs", "n_frames", "page_size", "n_pages", ... }`
- `GET /experiments/<id>/snapshots?page=<N>` → `{ "experiment_id", "page", "page_size", "n_pages", "n_frames", "next_page", "frames": [ { "index", "values": [<n_dofs floats>] }, ... ] }`. Pages are 1-based; fetch every page.

Run your CLI as `ruby /app/pod_cli.rb --base-url http://localhost:8000 --threshold 0.99 --output-dir /app/output`.

Milestone 1: for each **fixture** experiment (`is_fixture == true`; the others must be skipped entirely), fetch all snapshot pages and assemble the snapshot matrix `X` of shape `m × n`, where `m = n_dofs` and column `t` is the velocity field of frame `index = t`, ordered by frame index. Write `/app/output/<experiment_id>/snapshots_meta.json`:

```json
{
  "experiment_id": "<string>",
  "n_dofs": <int>,
  "n_frames": <int>,
  "frame_l2_norms": [<float per frame, in frame-index order>],
  "frobenius_norm": <float>
}
```

`frame_l2_norms[t]` is the Euclidean norm of frame `t`'s velocity field; `frobenius_norm` is the Frobenius norm of `X`. A non-fixture experiment must produce no output directory.
