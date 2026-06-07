FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# The system under test: a vendored networkx 3.4.2 source tree, installed editable
# so edits to the source take effect on import.
COPY networkx-src/ /app/networkx-src/
RUN python -m pip install --no-cache-dir -e /app/networkx-src

# Verifier-ONLY test dependencies are staged as wheels, not installed; tests/test.sh
# installs them offline from this wheel directory at verification time.
RUN python -m pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app
