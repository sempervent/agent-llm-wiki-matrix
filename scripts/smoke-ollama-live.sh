#!/usr/bin/env bash
# Opt-in live smoke: minimal Ollama-backed benchmark (network + local LLM).
# Prerequisites: `just ollama-gptoss-setup` (or Ollama reachable with gpt-oss:20b pulled).
# Does not run in default CI. Exits non-zero if probe fails or benchmark errors.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${ALWM_SMOKE_OLLAMA_OUT:-${TMPDIR:-/tmp}/alwm-smoke-ollama}"
HOST_URL="${OLLAMA_HOST:-http://127.0.0.1:11434}"
MODEL="${OLLAMA_MODEL:-gpt-oss:20b}"

export ALWM_FIXTURE_MODE=0
export OLLAMA_HOST="${HOST_URL}"
export OLLAMA_MODEL="${MODEL}"

echo "==> probe: ${OLLAMA_HOST} model=${OLLAMA_MODEL}"
PROBE="$(uv run alwm benchmark probe)"
echo "${PROBE}"
if ! echo "${PROBE}" | grep -q '"ollama_api_reachable": true'; then
  echo "ERROR: Ollama not reachable. Run: just ollama-gptoss-setup" >&2
  exit 1
fi
if ! echo "${PROBE}" | grep -q '"ollama_model_available": true'; then
  echo "ERROR: Model not available. Run: just ollama-gptoss-setup" >&2
  exit 1
fi

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

echo "==> benchmark run: benchmarks/v1/ollama.v1.yaml -> ${OUT_DIR}"
uv run alwm benchmark run \
  --definition "${ROOT}/benchmarks/v1/ollama.v1.yaml" \
  --output-dir "${OUT_DIR}" \
  --created-at "2026-04-17T00:00:00Z" \
  --run-id "smoke-ollama-live" \
  --no-fixture-mock

uv run alwm validate "${OUT_DIR}/manifest.json" benchmark_manifest
echo "ok: live Ollama smoke benchmark completed."
