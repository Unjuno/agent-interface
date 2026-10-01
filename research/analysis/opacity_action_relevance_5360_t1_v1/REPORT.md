# Issue #5360 T1 — action-relevant opacity

## Current disposition

`HOST_CONSTRUCTION_PASS / CONTAINER_FORMAL_STOP`. The finite deterministic host
experiment and corrected independent raw-only auditor pass; this is not the
requested OrbStack result, and the Issue remains open until the assigned
container runner and separate audit complete.

## H / T / D / C / U

- **H:** Action-relevant opacity rejects action-authorizing reads from aborted,
  rolled-back, uncommitted-at-consume, or generation-mismatched evidence while
  keeping presentation-only reads separate. A weak final-state comparator
  admits at least one invalid action history.
- **T:** Eight declared lifecycle patterns × two use roles × two policies = 32
  deterministic rows. The plan, source, outputs, and audit are retained beside
  this report. The container plan is exactly one runner invocation followed by
  one independent raw-only audit, with no retries.
- **D:** Attempts 05 and 06 are retained but superseded after review found
  scenario-label dependence, event chronology defects, and a rollback scenario
  that never committed before consumption. Attempt 07 is the corrected host
  construction gate: its independent auditor reconstructs validity from raw
  ordered events, checks strict unique sequence order, and rejects event-status,
  action-role, and generation mutation controls. Audit-only attempt 08 then
  re-audited the immutable attempt-07 raw, independently recomputed the exact
  decision object for both policies on all 32 rows, and rejected four mutation
  controls including a forged weak-comparator decision. Of six invalid action
  histories, the weak comparator admits five; strict opacity admits zero
  invalid histories and preserves two valid committed same-generation
  histories. Attempts 01–07 and their raw outputs/audits remain unchanged.
- **C:** Hand-authored synthetic histories; no production transaction manager,
  irreversible side effect, distributed commit, external process, or live GUI.
- **U:** Real concurrency semantics, retry behavior, distributed commit,
  irreversible effects, semantic completeness of generation IDs, real action
  effect, and runtime transfer.

## Execution boundary

Host: macOS 26.6.2 arm64, CPython 3.14.5, standard library only. Syntax checks
pass. Attempt 07 source SHA256: simulator
`0fb3cccb377a43d218c49d75fe1f7fe86c5508c09ea340ce8aae2350b5ed4549`,
original auditor `4e0e722ebb1fbabf02dcf6f92ed6b90a80de8e52b5dfd02265cbd183e010dd3a`.
Raw SHA256 `3fb5162d7f6e4d038e243068a829c024f7bf2b725f2d50cb39817b7ecc3fe30e`;
attempt-07 audit SHA256 `6d3fbef7ef4b08a66c6ec97269cc12e53d3f5ad43635849c3a6110178968e452`.
Attempt-08 auditor SHA256 `54253e2412225c59a6b7b410d5ec151facab357b3ee6d9fd77f73a128a6429b1`;
audit-only receipt SHA256 `6d3fbef7ef4b08a66c6ec97269cc12e53d3f5ad43635849c3a6110178968e452`.
A CPU-only OrbStack allocation is
requested in #5085. No Docker/OrbStack CLI or container invocation has occurred
for this allocation; until an exact coordinator grant, the formal result is
STOP, not PASS. Repository-wide local CI has not been run because the available
checkout is substantially behind current main.
