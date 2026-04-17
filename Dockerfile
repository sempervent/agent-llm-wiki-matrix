# Orchestration image: CLI, validators, and pipeline entrypoints.
# Multi-platform builds via docker buildx bake (see docker-bake.hcl).

FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install .

FROM base AS runtime

# Non-root user
RUN useradd --create-home --uid 1000 alwm
USER alwm
WORKDIR /workspace

ENV ALWM_REPO_ROOT=/workspace

ENTRYPOINT ["alwm"]
CMD ["--help"]

# Dev/test image: pytest + linters for Compose `test` profile (CI parity: prefer `just ci` locally).
FROM base AS test
RUN pip install -e ".[dev]"
RUN useradd --create-home --uid 1000 alwm
USER alwm
WORKDIR /workspace
ENV ALWM_REPO_ROOT=/workspace
ENTRYPOINT []
CMD ["python", "-m", "pytest", "-q", "tests/"]

# Optional: Playwright + Chromium for `browser-verify` Compose profile (not used by default CI).
FROM test AS browser-test
USER root
RUN pip install "playwright>=1.40" \
    && python -m playwright install --with-deps chromium
USER alwm
