FROM python:3.13-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# Agent runtime + verifier dependencies (pinned for reproducibility). The same
# image is shared by the agent and the verifier; the sandbox runs offline, so
# every dependency the verifier needs must be present here at build time.
RUN python -m pip install --no-cache-dir \
    mlflow==3.13.0 \
    scikit-learn==1.9.0 \
    pandas==2.3.3 \
    numpy==2.4.6 \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs available to the agent at start. Tests and the oracle solution are
# intentionally NOT copied into the image.
COPY dossier.md /app/dossier.md
COPY data.csv /app/data.csv
