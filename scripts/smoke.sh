#!/usr/bin/env bash
# Full-stack smoke: pytest (smoke marker) + host `alwm` paths + Docker Compose runtime paths.
# Does not use `set -e` so every phase runs; failures are collected and a recovery analysis prints at the end.
#
# Environment:
#   SMOKE_SKIP_DOCKER=1     — skip Docker phases (Python / host only).
#   ALWM_REPO_ROOT          — repo root (default: repository root containing this script).

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export ALWM_REPO_ROOT="${ALWM_REPO_ROOT:-$ROOT}"

SMOKE_TMP="$(mktemp -d "${TMPDIR:-/tmp}/alwm-smoke.XXXXXX")"
trap 'rm -rf "$SMOKE_TMP"' EXIT

FAILURES_FILE="$SMOKE_TMP/failures.txt"
: >"$FAILURES_FILE"

record_failure() {
  local name="$1" code="$2"
  printf '%s|%s\n' "$name" "$code" >>"$FAILURES_FILE"
}

run_step() {
  local name="$1"
  shift
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "smoke step: $name"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  "$@"
  local code=$?
  if [[ "$code" -eq 0 ]]; then
    echo "ok: $name"
    return 0
  fi
  echo "FAILED: $name (exit $code)" >&2
  record_failure "$name" "$code"
  return "$code"
}

smoke_host_benchmark_micro() {
  export ALWM_FIXTURE_MODE=1
  uv run alwm benchmark run \
    --definition fixtures/benchmarks/campaign_micro.v1.yaml \
    --output-dir "$SMOKE_TMP/host-micro" \
    --created-at "1970-01-01T00:00:00Z" \
    --run-id smoke-host-micro
  uv run alwm validate "$SMOKE_TMP/host-micro/manifest.json" benchmark_manifest
}

smoke_host_campaign() {
  export ALWM_FIXTURE_MODE=1
  rm -rf "$SMOKE_TMP/campaign"
  uv run alwm benchmark campaign run \
    --definition examples/campaigns/v1/minimal_offline.v1.yaml \
    --output-dir "$SMOKE_TMP/campaign" \
    --created-at "2026-04-17T00:00:00Z"
  uv run alwm validate "$SMOKE_TMP/campaign/manifest.json" benchmark_campaign_manifest
  uv run alwm validate "$SMOKE_TMP/campaign/campaign-summary.json" campaign_summary
}

smoke_docker_compose_config() {
  local p
  set -e
  for p in dev test benchmark benchmark-offline benchmark-ollama benchmark-probe benchmark-llamacpp browser-verify; do
    echo "  docker compose config --profile $p"
    docker compose --profile "$p" config --quiet
  done
}

recovery_lines_for() {
  local step="$1"
  case "$step" in
  pytest_smoke)
    cat <<'EOF'
- Ensure dev deps: `uv pip install -e ".[dev]"`.
- Re-run: `uv run pytest -m smoke -v`.
- If imports fail: check `uv sync` / venv and that you run from the repo root.
EOF
    ;;
  host_alwm_offline_benchmark_and_validate)
    cat <<'EOF'
- Run from repository root; `ALWM_REPO_ROOT` should point at the repo (default).
- Force mock path: `ALWM_FIXTURE_MODE=1 uv run alwm benchmark run ...`.
- Confirm `fixtures/benchmarks/campaign_micro.v1.yaml` and rubric paths resolve.
EOF
    ;;
  host_alwm_campaign_run_and_validate)
    cat <<'EOF'
- Same as host benchmark: repo root, `ALWM_FIXTURE_MODE=1` for offline mocks.
- Plan-only check: `uv run alwm benchmark campaign plan --definition examples/campaigns/v1/minimal_offline.v1.yaml --output-dir /tmp/alwm-cp --created-at 2026-04-17T00:00:00Z`.
EOF
    ;;
  docker_compose_config_all_profiles)
    cat <<'EOF'
- Install Docker Desktop / Colima / Rancher Desktop; ensure daemon is running (`docker info`).
- Validate manually: `docker compose --profile dev config --quiet`.
- If compose errors: use Docker Compose v2 (`docker compose`, not legacy `docker-compose`).
EOF
    ;;
  docker_dev_orchestrator_help)
    cat <<'EOF'
- Build image: `docker build -t agent-llm-wiki-matrix:local -f Dockerfile --target runtime .`
- Or: `docker compose --profile dev build orchestrator` then re-run smoke.
- Ensure Docker can bind-mount the repo (`PWD` → `/workspace` in Compose).
EOF
    ;;
  docker_benchmark_offline)
    cat <<'EOF'
- Requires runtime image `agent-llm-wiki-matrix:local` (built by compose run or Dockerfile).
- Service sets `ALWM_FIXTURE_MODE=1`; repo is mounted at `/workspace`.
- Host parity: `uv run alwm benchmark run --definition fixtures/benchmarks/offline.v1.yaml --output-dir out/local-smoke --created-at 1970-01-01T00:00:00Z --run-id local`.
EOF
    ;;
  *)
    cat <<'EOF'
- See `docs/workflows/smoke.md` and `docs/workflows/local-dev.md`.
EOF
    ;;
  esac
}

emit_failure_recovery_analysis() {
  if [[ ! -s "$FAILURES_FILE" ]]; then
    return 0
  fi
  echo ""
  echo "╔══════════════════════════════════════════════════════════════════════════╗"
  echo "║  Smoke failure recovery analysis                                         ║"
  echo "╚══════════════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Failure mode map (use with failed step ids below):"
  echo "  pytest_smoke          → Python venv / uv dev install / import errors"
  echo "  host_alwm_*           → repo root, ALWM_REPO_ROOT, ALWM_FIXTURE_MODE, fixture paths"
  echo "  docker_compose_*      → Docker daemon, Compose v2, docker-compose.yml syntax"
  echo "  docker_dev_*          → image build; stale cache → script uses --build"
  echo "  docker_benchmark_*    → runtime image + templates in Dockerfile; host parity: uv run alwm benchmark run …"
  echo ""
  echo "Failed steps and suggested recovery (work through in order):"
  echo ""
  local line name code
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    name="${line%%|*}"
    code="${line#*|}"
    echo "── $name (exit $code) ──"
    recovery_lines_for "$name"
    echo ""
  done <"$FAILURES_FILE"
  echo "General:"
  echo "  - Default CI parity: \`uv run just ci\` (ruff, mypy, pytest excluding integration)."
  echo "  - Compose profiles: \`just compose-help\`."
  echo ""
}

# --- Phase 1: Python smoke tests ---
run_step pytest_smoke uv run pytest -m smoke -v

# --- Phase 2: Host CLI — offline benchmark + manifest validation ---
run_step host_alwm_offline_benchmark_and_validate smoke_host_benchmark_micro

# --- Phase 3: Host CLI — campaign run + artifact validation ---
run_step host_alwm_campaign_run_and_validate smoke_host_campaign

# --- Phase 4–6: Docker (optional) ---
if [[ "${SMOKE_SKIP_DOCKER:-}" == "1" ]]; then
  echo ""
  echo "SMOKE_SKIP_DOCKER=1 — skipping Docker phases."
elif ! command -v docker >/dev/null 2>&1; then
  echo ""
  echo "docker not on PATH — skipping Docker phases (not counted as failure). Use SMOKE_SKIP_DOCKER=1 to silence."
else
  run_step docker_compose_config_all_profiles smoke_docker_compose_config
  # --build: ensure image matches current workspace (stale cache can omit CLI groups such as `alwm benchmark`).
  run_step docker_dev_orchestrator_help docker compose --profile dev run --rm --build orchestrator
  run_step docker_benchmark_offline docker compose --profile benchmark-offline run --rm --build benchmark-offline
fi

EXIT_CODE=0
if [[ -s "$FAILURES_FILE" ]]; then
  EXIT_CODE=1
fi

emit_failure_recovery_analysis

if [[ "$EXIT_CODE" -eq 0 ]]; then
  echo ""
  echo "All smoke steps passed (pytest + host alwm + optional Docker)."
else
  echo ""
  echo "Smoke finished with one or more failures; see recovery analysis above."
fi

exit "$EXIT_CODE"
