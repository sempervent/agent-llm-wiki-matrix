# Campaign summary: `campaign.examples.minimal_offline.v1`

- **title:** Minimal offline campaign (single suite, deterministic)
- **created_at:** `1970-01-01T00:00:00Z`
- **definition:** `examples/campaigns/v1/minimal_offline.v1.yaml`
- **definition_fingerprint:** `sha256:340780556158635e0b33298b726f530cbc86f7dcfdd8923934bbb14a0734e47b`

## Experiment fingerprints (axes)

Stable per-axis hashes for longitudinal grouping and comparability checks.

- **campaign_definition:** `sha256:340780556158635e0b33298b726f530cbc86f7dcfdd8923934bbb14a0734e47b`
- **suite_definitions:** `sha256:89fed34c06b5afbe00f18b22f21c268389fdf928f73f446796d8c19666514348`
- **provider_configs:** `sha256:69c4ef3c9876f8d46bd609d755baa1bb850cd8d9fdcbdee0748b6e10c36cf5f1`
- **scoring_configs:** `sha256:2c7f1b6d79305cde67076936152d80992802d413157de43143bac86c13c21fc8`
- **browser_configs:** `sha256:591cbc3aa572200862e2f336261f05849fe93c17d226a939565815d0cb075961`
- **prompt_registry_state:** `sha256:d409ed75b3cb355ac6727f09877d7ef98c40adce16e3e8284c6dcfe9c5c3db21`
- **fixture_mode_force_mock:** `True`
- **dry_run:** `False`
- **runs:** 1
- **succeeded / failed:** 1 / 0
- **git_commit:** `0a2acbfcd670589ccd2ab5723382194871097525`
- **git_describe:** `v0.1.0-1-g0a2acbf-dirty`

| # | run_id | suite | benchmark_id | eval axis | modes filter | status | mean score | cells |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| 0 | `campaign.examples.minimal_offline.v1__0000` | `fixtures/benchmarks/campaign_micro.v1.yaml` | `bench.fixtures.campaign.micro.v1` | suite_default | — | succeeded | 0.667276 | 1 |

## Longitudinal analysis

Each successful row is a standard benchmark run directory. Point longitudinal tooling at ``runs/*/manifest.json`` under this campaign root (see ``docs/workflows/longitudinal-reporting.md``).
