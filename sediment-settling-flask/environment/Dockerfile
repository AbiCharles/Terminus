FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# Agent + verifier runtime dependencies (pinned). Flask serves the observation
# API; scipy/numpy/pandas drive the fit; requests is the HTTP client.
RUN python -m pip install --no-cache-dir \
    flask==3.1.3 \
    scipy==1.17.1 \
    numpy==2.4.6 \
    pandas==3.0.3 \
    requests==2.34.2

# Verifier-ONLY test dependencies (pytest stack) staged as wheels; tests/test.sh
# installs them offline at verification time.
RUN python -m pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs: the experiment metadata database (agent-visible) and the Flask API
# source + its private observation store. The oracle solution and verifier tests
# are intentionally NOT copied into the image.
COPY spec.md /app/spec.md
COPY experiments.db /app/experiments.db
COPY start_api.sh /app/start_api.sh
COPY api/ /app/api/

# Auto-start the settling-observation API for interactive shells so the agent can
# consume it immediately at http://127.0.0.1:8000.
RUN chmod +x /app/start_api.sh \
    && printf '\n# Auto-start the settling-observation API.\nbash /app/start_api.sh >/dev/null 2>&1 || true\n' >> /etc/bash.bashrc
