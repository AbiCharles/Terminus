# Builder stage: synthesize the seeded SQLite earthquake catalog. The generator
# script and the true region parameters never reach the final image, so the agent
# cannot recover the answers from the environment.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2 AS builder

COPY generate_catalog.py /build/generate_catalog.py
RUN python /build/generate_catalog.py /build/catalog.db

# Final runtime stage.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

# Agent runtime toolchain: Ruby (the agent writes the CLI as an executable Ruby
# script using the sqlite3 gem), the SQLite dev headers + shell the gem links
# against, and the recording runtime (tmux, asciinema) the harness expects. The
# verifier uses the base image's Python standard library (sqlite3, math) for its
# independent reference; no third-party Python runtime libraries are required.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ruby-full \
        ruby-dev \
        libsqlite3-dev \
        build-essential \
        pkg-config \
        sqlite3 \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/* \
    && gem install sqlite3 --no-document -- --enable-system-libraries

# Verifier-ONLY test dependencies (pytest stack) staged as wheels and NOT installed:
# the agent works in C and needs none of them. Each milestone's tests/test.sh installs
# them offline (--no-index) from this wheel directory at verification time, so the agent
# runtime image never carries the test tooling.
COPY requirements.lock /tmp/requirements.lock
RUN python -m pip download --no-cache-dir --require-hashes --no-deps -d /opt/verifier-wheels -r /tmp/requirements.lock

WORKDIR /app

# The provided catalog the agent's CLI reads. Tests seed their own small
# databases at verification time; this is the working catalog for development.
COPY --from=builder /build/catalog.db /app/catalog.db
