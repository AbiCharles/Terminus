# Sanctioned, digest-pinned base. Python is present only so the pytest-based
# verifier can drive the C harness; the task itself is pure C.
FROM python:3.13-slim-bookworm@sha256:e4fa1f978c539608a10cdf74700ac32a3f719dfc6e8b6b6001da82deb36302a2

# Required by the agent runtime (tmux, asciinema); gcc provides the C toolchain
# and libasan/libubsan provide the AddressSanitizer/UndefinedBehaviorSanitizer
# runtimes the verifier links the candidate allocator against. Installed at build
# time (the runtime sandbox has no network).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        gcc \
        libc6-dev \
        libasan8 \
        libubsan1 \
    && rm -rf /var/lib/apt/lists/*

# Verifier-ONLY test dependencies (pytest stack) are staged as wheels rather than
# installed, so the agent environment does not carry test tooling. Each milestone's
# tests/test.sh installs them offline from this wheel directory at verification time.
RUN pip download --no-cache-dir -d /opt/wheels \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Task inputs available to the agent at start: the allocator contract header and a
# non-functional stub to implement. The test harness and oracle are intentionally
# NOT copied into the image.
COPY allocator.h /app/allocator.h
COPY allocator.c /app/allocator.c
