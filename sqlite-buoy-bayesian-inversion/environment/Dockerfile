# Builder stage: generate the seeded SQLite observation database. The generator
# script and the true offset/drift parameters never reach the final image, so the
# agent cannot recover the answers from the environment.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2 AS builder

# Builder needs only numpy to synthesize the database (kept lean via its own lock).
COPY requirements-build.lock /tmp/requirements-build.lock
RUN pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements-build.lock

COPY generate_observations.py /build/generate_observations.py
RUN python /build/generate_observations.py /build/observations.db

# Final runtime stage.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

# Required by the agent runtime — missing these makes agent runs fail silently.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# Agent + verifier runtime dependencies (numpy for the inversion; scikit-learn and
# mlflow for logging/registering the calibration model; sqlite3 is stdlib). The
# verifier also needs them to recompute the reference and to load the registered
# model. Installed from a fully hashed lockfile.
COPY requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock

# Verifier-ONLY test dependencies (pytest stack) are staged as wheels rather than
# installed, so the agent environment does not carry test tooling. Each milestone's
# tests/test.sh installs them offline from this wheel directory at verification time.
RUN pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs available to the agent at start. Tests and the oracle solution are
# intentionally NOT copied into the image.
COPY mission_notebook.md /app/mission_notebook.md
COPY --from=builder /build/observations.db /app/observations.db
