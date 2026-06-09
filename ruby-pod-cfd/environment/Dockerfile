# --- builder stage: generate deterministic CFD snapshot fixtures with numpy ---
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2 AS fixturegen
RUN pip install --no-cache-dir numpy==2.1.3
COPY fixtures_gen/generate_fixtures.py /build/generate_fixtures.py
RUN python /build/generate_fixtures.py /build/fixtures

# --- final runtime stage ---
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ruby ruby-dev build-essential curl tmux asciinema \
        libyaml-dev zlib1g-dev libffi-dev libssl-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Build/bundle the provided Rails CFD API and load the fixtures it serves.
WORKDIR /opt/api
COPY api/Gemfile api/Gemfile.lock ./
RUN gem install bundler --no-document && bundle config set --local frozen true && bundle install
COPY api/ /opt/api/
COPY --from=fixturegen /build/fixtures /opt/api/fixtures

# Idempotent API launcher + auto-start for the agent's login shells.
COPY start_api.sh /opt/start_api.sh
RUN chmod +x /opt/start_api.sh \
    && printf '#!/bin/bash\n/opt/start_api.sh >/dev/null 2>&1 &\n' > /etc/profile.d/pod_api.sh \
    && chmod +x /etc/profile.d/pod_api.sh

# Verifier-only deps (numpy reference + pytest) staged as wheels; installed offline at test time.
RUN pip download --no-cache-dir -d /opt/wheels \
    numpy==2.1.3 \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Agent starting point.
COPY pod_cli_stub.rb /app/pod_cli.rb
