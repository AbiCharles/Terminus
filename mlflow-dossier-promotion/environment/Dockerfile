FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# Agent + verifier runtime dependencies (pinned for reproducibility). These are
# needed both by the agent (to train/log models) and by the verifier (to retrain
# the reference candidates), so they are installed into the image.
RUN python -m pip install --no-cache-dir \
    mlflow==3.13.0 \
    scikit-learn==1.9.0 \
    pandas==2.3.3 \
    numpy==2.4.6

# Verifier-ONLY test dependencies (pytest stack) are staged as wheels rather than
# installed, so the agent environment does not carry test tooling. tests/test.sh
# installs them offline from this wheel directory at verification time.
RUN python -m pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs available to the agent at start. Tests and the oracle solution are
# intentionally NOT copied into the image.
COPY dossier.md /app/dossier.md
COPY data.csv /app/data.csv
