# Builder stage: generate the seeded DuckDB database. The generator script and
# its true signal parameters never reach the final image, so the agent cannot
# recover the answers from the environment.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2 AS builder

RUN pip install --no-cache-dir \
    numpy==2.4.6 \
    duckdb==1.4.4

COPY generate_measurements.py /build/generate_measurements.py
RUN python /build/generate_measurements.py /build/measurements.duckdb

# Final runtime stage.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

# Required by the agent runtime — missing these makes agent runs fail silently.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# Agent + verifier runtime dependencies (pinned). The agent needs these to query
# the database and compute the analysis; the verifier needs them to recompute the
# reference answers independently.
RUN pip install --no-cache-dir \
    numpy==2.4.6 \
    scipy==1.16.3 \
    pandas==2.3.3 \
    duckdb==1.4.4 \
    mlflow==3.13.0

# Verifier-ONLY test dependencies (pytest stack) are staged as wheels rather than
# installed, so the agent environment does not carry test tooling. Each milestone's
# tests/test.sh installs them offline from this wheel directory at verification time.
RUN pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Only the database is shipped to the agent — there are no raw measurement files.
COPY --from=builder /build/measurements.duckdb /app/measurements.duckdb
