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

# Agent runtime toolchain. The agent solves the task in C++: g++ to compile, the
# SQLite C library to read /app/observations.db, and the nlohmann JSON header to read
# and write the JSON artifacts. tmux + asciinema are required by the agent harness.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        g++ \
        libsqlite3-dev \
        nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

# Verifier-ONLY dependencies (pinned), staged as wheels and NOT installed: the agent
# works in C++ and needs none of these. The pytest verifier recomputes the reference
# posterior independently with numpy; each milestone's tests/test.sh installs these
# offline (--no-index) from this wheel directory at verification time, so the agent
# runtime image never carries the test tooling.
RUN pip download --no-cache-dir --dest /opt/verifier-wheels \
    numpy==2.4.6 \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs available to the agent at start. Tests and the oracle solution are
# intentionally NOT copied into the image.
COPY mission_notebook.md /app/mission_notebook.md
COPY --from=builder /build/observations.db /app/observations.db
