# Smoke workflow (`just smoke`)

End-to-end checks beyond unit tests: Python smoke markers, host CLI paths, and (when Docker is available) Compose + runtime image behavior.

## What runs

| Phase | Step id | What it checks |
| --- | --- | --- |
| 1 | `pytest_smoke` | `uv run pytest -m smoke -v` (`tests/test_smoke.py`) |
| 2 | `host_alwm_offline_benchmark_and_validate` | `alwm benchmark run` on `fixtures/benchmarks/campaign_micro.v1.yaml` + `alwm validate` manifest |
| 3 | `host_alwm_campaign_run_and_validate` | `alwm benchmark campaign run` on `examples/campaigns/v1/minimal_offline.v1.yaml` + validate campaign artifacts |
| 4 | `docker_compose_config_all_profiles` | `docker compose config --quiet` for each profile used in `just compose-help` |
| 5 | `docker_dev_orchestrator_help` | `docker compose --profile dev run --rm --build orchestrator` → `alwm --help` in the runtime image |
| 6 | `docker_benchmark_offline` | `docker compose --profile benchmark-offline run --rm --build benchmark-offline` (fixture benchmark to `out/benchmark-offline`) |

Phases 4–6 are skipped when:

- `SMOKE_SKIP_DOCKER=1`, or
- `docker` is not on `PATH` (informational skip; not treated as a failure).

## Failure recovery analysis

The script runs **all** phases even after a failure (no `set -e` on the whole run). Any non-zero step is recorded; at the end a **Smoke failure recovery analysis** block lists each failed step id and concrete recovery hints (venv, repo root, Docker daemon, image rebuild, host-parity commands).

Rough **failure mode** mapping:

| Failure prefix | Likely area |
| --- | --- |
| `pytest_smoke` | Python env / dev deps / imports |
| `host_alwm_*` | Wrong cwd, `ALWM_REPO_ROOT`, missing fixtures, `ALWM_FIXTURE_MODE` |
| `docker_compose_*` | Docker not running, Compose v2, invalid `docker-compose.yml` |
| `docker_dev_*` / `docker_benchmark_*` | Stale image (script uses `--build`), Dockerfile, bind-mount; runtime image includes bundled `templates/` under `/usr/local/lib/python3.11/templates` so `alwm benchmark run` works without relying on repo layout inside site-packages |

## Environment

| Variable | Meaning |
| --- | --- |
| `SMOKE_SKIP_DOCKER` | Set to `1` to run only pytest + host `alwm` steps (e.g. agents without Docker). |
| `ALWM_REPO_ROOT` | Repository root; defaults to the directory containing `scripts/smoke.sh` parent. |

## CI

Default **`just ci`** remains **ruff + mypy + full pytest** (excluding `tests/integration/`). Smoke is a **supplementary** full-application gate for developers and release checks; run `just smoke` before merges that touch CLI, benchmarks, campaigns, or Docker.
