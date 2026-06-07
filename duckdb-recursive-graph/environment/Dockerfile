FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# DuckDB command-line shell (pinned). This is the agent's tool for the task: the
# deliverable is SQL run against /app/graph.duckdb via this `duckdb` CLI, so no
# Python is required to solve the task. Downloaded for the build architecture.
ARG DUCKDB_VERSION=1.5.3
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip ca-certificates \
    && arch="$(dpkg --print-architecture)" \
    && case "$arch" in \
         amd64) names="amd64" ;; \
         arm64) names="arm64 aarch64" ;; \
         *) names="$arch" ;; \
       esac \
    && ok=0 \
    && for n in $names; do \
         if curl -fsSL -o /tmp/duckdb_cli.zip \
              "https://github.com/duckdb/duckdb/releases/download/v${DUCKDB_VERSION}/duckdb_cli-linux-${n}.zip"; then \
           ok=1; break; \
         fi; \
       done \
    && [ "$ok" = 1 ] || { echo "duckdb CLI download failed for arch $arch"; exit 1; } \
    && unzip -o /tmp/duckdb_cli.zip -d /usr/local/bin \
    && rm /tmp/duckdb_cli.zip \
    && chmod +x /usr/local/bin/duckdb \
    && duckdb --version \
    && apt-get purge -y curl unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Verifier-ONLY dependencies (pinned). The pytest verifier recomputes ground truth
# independently using the DuckDB Python API + pandas/numpy; these are not needed to
# solve the task and are not the task's language (the agent works in SQL).
RUN python -m pip install --no-cache-dir \
    duckdb==1.5.3 \
    pandas==2.3.3 \
    numpy==2.4.6

# Verifier-ONLY test dependencies are staged as wheels, not installed; tests/test.sh
# installs them offline from this wheel directory at verification time.
RUN python -m pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs available to the agent at start. Tests and the oracle solution are
# intentionally NOT copied into the image.
COPY graph.duckdb /app/graph.duckdb
COPY spec.md /app/spec.md
