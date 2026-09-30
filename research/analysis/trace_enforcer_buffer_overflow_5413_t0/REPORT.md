# Result: buffer overflow can hide action-relevant invalidation

## Disposition

`PASS_CONSTRUCTION_ONLY_HOST`; not a Docker/OrbStack result and not a live
runtime result. The finite test discriminated silent evidence loss from an
overflow-to-UNKNOWN policy exactly as hypothesized, while also exposing the
policy's false-rejection cost on irrelevant telemetry overflow.

## Executed evidence

- Base main at source construction: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`.
- Source freeze commit: `b09bfebb8476d82e9cdc817d2652a9519db8c753`.
- Candidate runner invocation: **1**. No candidate retry or tuning.
- Host construction tests: **4/4 PASS** on CPython 3.14.5, standard library.
- Runner matrix: **6 rows** (3 traces x 2 policies).
- Raw-only audit: `PASS`, 6 rows, zero errors. The auditor was invoked twice
  against the identical immutable raw file (initial result and a readback
  verification); no source or raw row changed between invocations.
- Corruption controls: **5/5 rejected**. The five controls were duplicate
  cell, missing cell, flipped decision, erased overflow cause, and false
  no-overflow flag. The corruption-control command was also invoked twice;
  both produced the same five rejections.
- `git diff --check`: PASS before execution and after the source freeze.
- Formal Docker/OrbStack invocations: **0**. No image inspection, pull, or
  container launch was performed.

## Matrix outcome

| Trace | `FAIL_CLOSED` | `DROP_NEWEST` baseline |
|---|---|---|
| Exact matching evidence, capacity not exceeded | PASS, effect emitted | PASS, effect emitted |
| External mutation is the third event at capacity 2 | UNKNOWN, no effect | **PASS, stale effect emitted** |
| Irrelevant telemetry is the third event at capacity 2 | UNKNOWN, no effect | PASS, effect emitted |

The second row is the counterexample: keeping only the first two evidence
events silently loses `EXTERNAL_MUTATION(target=t, epoch=8)` and admits a commit
bound to epoch 7. The third row quantifies the corresponding conservative
availability cost. It motivates a distinct follow-up comparison of
action-relevant invalidation preservation/watermarks; it does not justify
weakening the frozen fail-closed policy in this result.

## Reproduction

```text
python3 -B -m unittest discover -s research/analysis/trace_enforcer_buffer_overflow_5413_t0 -p 'test_*.py' -v
python3 -B research/analysis/trace_enforcer_buffer_overflow_5413_t0/experiment.py > research/analysis/trace_enforcer_buffer_overflow_5413_t0/raw/host-formal-01.jsonl
python3 -B research/analysis/trace_enforcer_buffer_overflow_5413_t0/audit.py research/analysis/trace_enforcer_buffer_overflow_5413_t0/raw/host-formal-01.jsonl > research/analysis/trace_enforcer_buffer_overflow_5413_t0/raw/audit-01.json
python3 -B research/analysis/trace_enforcer_buffer_overflow_5413_t0/corruption_controls.py research/analysis/trace_enforcer_buffer_overflow_5413_t0/raw/host-formal-01.jsonl > research/analysis/trace_enforcer_buffer_overflow_5413_t0/raw/corruption-controls-01.json
```

## Hashes

Frozen candidate sources are listed in [PLAN.md](PLAN.md). Executed raw bytes:

- `host-formal-01.jsonl`: `f4569721d5a39944dab21a55c6270403e9f69a75b815cc7183d0dda980c15da0`
- `audit-01.json`: `9cf69c290422340136cf31c2f8a91d8fa4d12289019fb161bf06d31cff11c8ae`
- `corruption-controls-01.json`: `d14489f17e8b1c2e919e29a28c364c6a276c24b97be0a788a24c57e35f74647d`

## Interpretation and limits

This demonstrates only that this hand-authored bounded policy model contains a
failure surface that the silent-drop baseline misses. It does not verify a
production buffer, event ordering, a real GUI, partial observation, intent
preservation, latency, or task effect. The lossy baseline is deliberately
constructed, and the `UNKNOWN` rule may be over-conservative. No runtime or
product safety claim follows.

Repository-wide analysis/workspace indexes and hosted CI have not run in this
sparse checkout. They remain integration gates. The exact source and outputs
must be read back in GitHub through a reviewable PR before treating this as a
shared repository result. A separate bounded Docker allocation is still
needed for container reproducibility; #5085's current lane belongs to another
experiment and grants no access to OrbStack.
