# Multi-agent parallel work

This repo is often edited by **multiple humans or coding agents** at once. These rules reduce merge pain and silent overlap.

## Branch strategy

- **One logical change per branch** (feature, fix, docs-only governance pass). Avoid long-lived “kitchen sink” branches.
- **Name branches by scope**, e.g. `bench/registry-fix`, `docs/agents-governance`, `browser/playwright-opts`.
- **Rebase or merge `main` frequently** before large edits so schema/CLI drift is caught early.

## File ownership zones (soft boundaries)

| Zone | Typical paths | Conflict risk |
| --- | --- | --- |
| **CLI surface** | `src/agent_llm_wiki_matrix/cli.py` | High—coordinate before adding commands/flags. |
| **Contracts** | `schemas/v1/`, `artifacts.py`, `models.py` | High—serial changes preferred. |
| **Benchmarks** | `benchmarks/v1/`, `fixtures/benchmarks/`, `benchmark/` | Medium—merge defs and runner separately when possible. |
| **Prompts** | `prompts/registry.yaml`, `prompts/versions/` | Medium—add new ids; avoid reusing ids for different text. |
| **Browser** | `src/agent_llm_wiki_matrix/browser/` | Medium—runner vs formatting vs CLI. |
| **Docs** | `docs/` (except simultaneous edits to same file) | Low–medium—split by file. |
| **Examples / fixtures** | `examples/`, `fixtures/` | Medium if same filenames. |

**Rule:** If two agents touch the same **file** in one PR, split work or sequence merges.

## Conflict avoidance

- **Do not rename** `alwm` subcommands or flags without an explicit migration note in `docs/implementation-log.md` and README.
- **Prefer additive changes** (new schema field with default, new CLI flag) over breaking renames.
- **Prompt text:** prefer **`prompt_ref`** in benchmark YAML over duplicating `text:` (see `AGENTS.md`).
- **Run `just ci`** before push; fix conflicts locally—do not merge broken `main`.

## Merge order (suggested)

1. **Contracts first** (schemas, `artifacts.py`, Pydantic) if other work depends on them.
2. **Implementation** (library + tests).
3. **CLI** (thin wrappers over library).
4. **Docs** (README, AGENTS, architecture, workflows).

Docs-only PRs can merge anytime; if they change command names, merge **after** or **with** code.

## Required handoff summary (for agent-to-agent or PR description)

Paste this block and fill it in:

```text
## Handoff
- Branch:
- Scope (1–2 sentences):
- Files touched (paths):
- Commands run (exact): e.g. just ci; alwm … --help
- Contracts changed: yes/no (schemas / artifacts kinds)
- Follow-ups: none / list
- Known gaps: none / list
```

## Related

- Operating manual: `AGENTS.md`
- Capability labels: `docs/audits/capability-classification.md` (do not claim “complete” without evidence)
