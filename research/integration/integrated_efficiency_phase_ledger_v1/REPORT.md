# Integrated efficiency phase ledger v1 — retained result

Task: `INTEGRATED-EFFICIENCY-PHASE-LEDGER-20260917-001`  
Issue: #836  
Immutable BASE: `f9989b833611fb9cb8708007445b94a95d70c516`

Disposition: **`PASS_PHASE_LEDGER_RECONSTRUCTED_SCOPED`**.

Formal runner invoked exactly once; reruns 0. No model, GUI, provider, network or task-input action occurred. This allocation reconstructs the already-retained #57 comparison into an explicit arm × phase × work ledger.

## Exact reconciliation

Retained source blobs:
- integrated report `57954e7608f823ec031600a12e0062eeceafdcf4`
- retained audit `e32fae1480f56e296a47ec7f4dd57ad21d09e35a`
- #829 phase-complete wall result `89e8bc08d4d81f93a496eac83437ad77a06f1214`

All 21 frozen rows reconcile:
- 3 schema preflights + 18 task rows;
- 17 planner generations/model calls total;
- 14 model-visible grounding images;
- global usage `input=153470`, `cached=4864`, `output=2435`, `reasoning=837`;
- per-arm input `plain=63128`, `ephemeral=63779`, `persistent=26563`;
- phase-complete elapsed `plain=62754.198912 ms`, `ephemeral=80378.859099 ms`, `persistent=51627.109593 ms`.

Cached input remains a provider-reported subset of input and is reported separately, never added to or subtracted from input totals.

## Arm totals

| arm | input | cached | output | reasoning | planner generations | model images | local observations | durable calls | phase-complete ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plain | 63,128 | 0 | 754 | 306 | 7 | 6 | 105 | 36 | 62,754.198912 |
| ephemeral | 63,779 | 4,864 | 1,209 | 404 | 7 | 6 | 129 | 96 | 80,378.859099 |
| persistent | 26,563 | 0 | 472 | 127 | 3 | 2 | 136 | 114 | 51,627.109593 |

Persistent is lower than both controls on input, output, reasoning, planner generations and model-visible images. It is **higher** than plain on local observations and durable calls. The result therefore supports a narrower architectural statement: persistent reuse shifts work from model-visible/model-boundary operations into local runtime operations; it does not make every work dimension smaller.

## Persistent phase ledger

| phase | input | output | reasoning | generations | images | local observations | durable calls | elapsed ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preflight | 7,965 | 143 | 28 | 1 | 0 | 0 | 0 | 7,495.828365 |
| acquisition task-1 | 9,299 | 168 | 53 | 1 | 1 | 21 | 16 | 11,024.952714 |
| repeated A tasks2-3 | 0 | 0 | 0 | 0 | 0 | 47 | 40 | 8,231.816299 |
| invalidation/repair task-4 | 9,299 | 161 | 46 | 1 | 1 | 22 | 18 | 12,341.465157 |
| repeated B tasks5-6 | 0 | 0 | 0 | 0 | 0 | 46 | 40 | 12,533.047058 |

Only the persistent route labels `reuse`/`repair` are interpreted as actual warm reuse/repair. Control-arm repeated schedule phases remain cold routes and are not relabelled as warm behavior.

## Integrity

- source-first freeze commit: `e9c1146c0e2993d54e8d2f47c44ee105653c705f`
- local FREEZE SHA-256: `67cbc5a6fe74d96edb31555494e80c49856caf2e17a8363e75a1be5434b82aa3`
- RESULT SHA-256: `f8fc677a10aced9bd8fd33de523600412419dc308aa3498cd46a17e7e9565b9f`
- AUDIT SHA-256: `9ed1a3329d9d297a394567b2b37e0e773db972b1298a5a593803340606f2113c`
- independent VERIFY SHA-256: `7f5e15785b6daa81758ef63e8ed680e2a0da21913a3656ca01b002297453a6cc`
- corruption controls SHA-256: `4083c1753ff7e6d77da461fc5fdc8a28b5b848a25a37b4234ff8db35258867ae`, reject 5/5.

## Boundary

This is retained-evidence accounting, not a new causal performance allocation. Fewer model-visible units may simply follow from fewer model calls. Local observation/durable-call counts are not commensurate with token, latency, energy or monetary cost. One Chromium allocation does not establish population reliability, human tempo, second-domain gain, or a general total-cost frontier.

The minimum reporting shape for the next fresh #57 integrated allocation should retain this multidimensional arm×phase ledger directly rather than requiring posthoc reconstruction.
