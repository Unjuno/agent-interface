# Issue #6045 T0 — container method result

## Disposition

`PASS_METHOD_SCOPED` for the frozen 18-row synthetic measurement contract. This is the first-row method test only. It is not a live agent, GUI/game, safety, latency-benefit, or task-quality result. The run used the requested Docker/OrbStack container path: one CPU-bounded candidate container, followed after exit 0 by one separate read-only raw-only auditor container. Both used `--rm`; retries=0.

## H / T / D / C / U

- **H:** Delivery-AoI or onset→effect latency alone can mis-rank routes; a source-to-relevant-effect lineage card can expose the reversal without resetting for irrelevant activity or attributing model use without evidence.
- **T:** Executed the frozen finite 18-row fixture once in the candidate and once in the independent auditor, both in separate `linux/arm64` containers from the pinned CPython Alpine image, no network, bounded CPU/memory/PIDs, no user-data mounts. The auditor independently reconstructed all 18 rows and validated the hash-bound candidate manifest. Mutation controls in the candidate package regenerate the ledger hash after corruption so semantic rejection—not merely stale-digest rejection—is exercised.
- **D:** Candidate exit 0, emitted 18 rows. Independent auditor exit 0, `PASS_METHOD_SCOPED`, `errors=[]`. The two planted witness pairs showed the expected ranking reversals. Unattributed multiple observations and uncertain clock order withheld scalar age; an interval crossing the deadline produced UNKNOWN; irrelevant/dispatch-only/unrelated effects did not reset the opportunity. Local suite 8/8 and source/image/freeze checks passed.
- **C:** All event times are synthetic milliseconds. For intervals, age is emitted only after strict source-before-effect order is proved; ON_TIME requires the latest possible effect no later than the deadline, LATE requires the earliest possible effect after it, otherwise UNKNOWN. A single-source fixture declaration is not evidence of causal use by a real model.
- **U:** No runtime/task efficacy, real causal ancestry, action safety, human tempo, model/game/GUI/input, GPU, or production effect was tested. No empirical claims follow from this fixture.

## Execution accounting

- Base main: `39cff8c45e3df04f1f7e98962b043c3fb0179ed2`.
- Branch: `research/opportunity-conditioned-actuated-info-6045-t0-20261002`.
- Frozen inputs and source SHA-256 values: `FREEZE.json`.
- Image: `python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`; image inspect receipt confirms local image ID `sha256:34d4d54d6f68a1980ad02433a5078d998ab394d55c97d953efa50b442135baf2`, `linux/arm64`.
- Raw ledger SHA-256: `804f44fb404289ccb238ff66f73fd176e296a47d212539d9281573542921a96d`.
- Fixture SHA-256: `e2c89bdede9e2ac61ab112defd30783173a50bccbc5ab0c42d1f675697beadfb`.
- Candidate/auditor exit receipts and stdout/stderr: `results/OPPORTUNITY-CONDITIONED-ACTUATED-INFO-6045-T0-20261002-01/host/`.
- Candidate raw ledger and manifest: `results/OPPORTUNITY-CONDITIONED-ACTUATED-INFO-6045-T0-20261002-01/output/`.
- `--rm` removed each completed container, so persistent container IDs/inspect JSON were not retained. No existing container or OrbStack VM was inspected, stopped, signalled, or modified.
- The queue had no separate owner-bound grant for this exact allocation at execution time. This run proceeded under the user's explicit instruction to conduct the Issue experiment in a container. It does not claim a #5085 slot, exclusive lease, or conflict-free host capacity. Preserve this coordination caveat for integration review.

## Local CI / integrity

- T0 package: 8/8 tests.
- Existing Analysis Index workflow regressions: endogenous-demand T0 8/8; selection-aware shadow-audit T1 12/12.
- Research workspace index tests: 1/1; committed research namespace index: 152/152 directories reachable.
- Analysis generated index: all 365 prior links preserved and this report added, total 366; this was independently diff-checked against the sparse checkout's base-main index. The full-tree `check_index.py` action remains the authoritative remote check.
- All 18 package artifacts listed in `SHA256SUMS` verify; frozen source hashes, `git diff --check`, JSON/Python syntax checks passed.
- The first test command launched from repository root failed because the package tests require the package directory as their import root. The documented package-cwd invocation then passed 8/8; no candidate/auditor rerun occurred.

## Reproduction

From this directory, first run:

```sh
python3 -B -m unittest discover -s tests -v
```

The recorded one-shot candidate/auditor container outputs are preserved under `results/`; do not rerun this consumed allocation. A new candidate execution requires a distinct allocation and fresh source/image/resource gates.
