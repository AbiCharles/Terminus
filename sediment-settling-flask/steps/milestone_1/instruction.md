We ran a settling-column experiment and I need the analysis pipeline built around experiment 1. The full contract — input locations, the API shape, the unit conversion, and the model and report format — is in `/app/spec.md`; read it first.

Two inputs: experiment metadata and sensor calibration live in a SQLite database at `/app/experiments.db`, and the time-series observations come from a small local HTTP API at `http://127.0.0.1:8000` (its source is in `/app/api/`; if it isn't already up, start it with `bash /app/start_api.sh`). Everything targets `experiment_id = 1`. Over three milestones you'll (1) pull the experiment's metadata, (2) retrieve and clean its observations from the API, and (3) fit the sedimentation model and report the parameters. Write each output under `/app/output/`.

Milestone 1: write `/app/output/metadata.json` for experiment 1 as defined in `/app/spec.md` — the experiment's fields joined with its sensor's calibration constants from `/app/experiments.db`.
