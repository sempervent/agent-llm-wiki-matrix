#!/usr/bin/env bash
# Start Compose Ollama, pull gpt-oss:20b into the bind-mounted store, verify via `alwm benchmark probe`.
# Run from repo root. See docs/workflows/benchmarking.md (Ollama / gpt-oss).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL="${OLLAMA_PULL_MODEL:-gpt-oss:20b}"
HOST_URL="${OLLAMA_PROBE_HOST:-http://127.0.0.1:11434}"

echo "==> Starting Ollama (profile benchmark-ollama)…"
docker compose --profile benchmark-ollama up -d ollama

echo "==> Waiting for Ollama to accept CLI…"
for _ in $(seq 1 90); do
  if docker compose --profile benchmark-ollama exec -T ollama ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker compose --profile benchmark-ollama exec -T ollama ollama list >/dev/null 2>&1; then
  echo "ERROR: Ollama did not become ready in time." >&2
  exit 1
fi

echo "==> Pulling ${MODEL} (stored under ./.ollama-models by default)…"
docker compose --profile benchmark-ollama exec -T ollama ollama pull "${MODEL}"

echo "==> Installed models:"
docker compose --profile benchmark-ollama exec -T ollama ollama list

echo "==> Verifying API + model tag from host (${HOST_URL})…"
export OLLAMA_HOST="${HOST_URL}"
export OLLAMA_MODEL="${MODEL}"
OUT="$(uv run alwm benchmark probe)"
echo "${OUT}"
if ! echo "${OUT}" | grep -q '"ollama_api_reachable": true'; then
  echo "ERROR: Ollama HTTP API not reachable at ${HOST_URL} (is port 11434 published?)" >&2
  exit 1
fi
if ! echo "${OUT}" | grep -q '"ollama_model_available": true'; then
  echo "ERROR: Model ${MODEL} not listed as available (pull may have failed or name mismatch)." >&2
  exit 1
fi

echo "ok: Ollama is up and ${MODEL} is available."
