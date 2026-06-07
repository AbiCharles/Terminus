FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# Agent + verifier runtime dependencies (pinned). Flask serves the observations
# API; scipy/numpy/pandas drive the fit; requests is available for the HTTP client.
RUN python -m pip install --no-cache-dir \
    flask==3.1.0 \
    requests==2.32.3 \
    scipy==1.17.1 \
    numpy==2.4.6 \
    pandas==2.3.3

# Verifier-ONLY test dependencies are staged as wheels, not installed; tests/test.sh
# installs them offline from this wheel directory at verification time.
RUN python -m pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs: the SQLite metadata DB, the API source + its private data store, the
# launcher, and the spec. Tests and the oracle solution are NOT copied in.
COPY experiments.db /app/experiments.db
COPY api/ /app/api/
COPY start_api.sh /app/start_api.sh
COPY spec.md /app/spec.md

# Auto-start the API for interactive (agent) login shells, and make the launcher
# executable. The oracle and the verifier also invoke it explicitly (idempotent).
RUN chmod +x /app/start_api.sh \
    && printf '%s\n' 'bash /app/start_api.sh >/dev/null 2>&1 || true' > /etc/profile.d/sediment_api.sh
