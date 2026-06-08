# Builder stage: generate the seeded DuckDB database. The generator script and
# its true signal parameters never reach the final image, so the agent cannot
# recover the answers from the environment.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2 AS builder

# Builder deps (numpy + duckdb) from a fully hashed lockfile.
COPY requirements-build.lock /tmp/requirements-build.lock
RUN pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements-build.lock

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

# Agent + verifier runtime dependencies. The agent needs these to query the
# database and compute the analysis; the verifier needs them to recompute the
# reference answers independently. Installed from a fully hashed lockfile
# (requirements.in -> requirements.lock via uv) for reproducible builds.
COPY requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock

# Verifier test dependencies (pytest stack) are preinstalled into the image at
# build time so verification needs no network and no install step — each
# milestone's tests/test.sh simply runs pytest.
RUN pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Only the database is shipped to the agent — there are no raw measurement files.
COPY --from=builder /build/measurements.duckdb /app/measurements.duckdb
