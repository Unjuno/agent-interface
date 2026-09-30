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
- **D:** Host attempt 05 audit is `PASS_T1_SCOPED`: 4 invalid action-read cases
  pass the weak comparator, 0 pass strict opacity, and 3 valid same-generation
  action reads remain admissible. The auditor rejects abort-status,
  action-role/provenance, and generation corruption controls. Host attempts
  01–04 and their failed auditor outcomes are preserved unchanged.
- **C:** Hand-authored synthetic histories; no production transaction manager,
  irreversible side effect, distributed commit, external process, or live GUI.
- **U:** Real concurrency semantics, retry behavior, distributed commit,
  irreversible effects, semantic completeness of generation IDs, real action
  effect, and runtime transfer.

## Execution boundary

Host: macOS 26.6.2 arm64, CPython 3.14.5, standard library only. Syntax checks
pass. Current-main source freeze for the candidate is `cf342db30a3ac8e28b747d45b3805c5af1e72fac`; source commit is
`ebfcb4cee5ce69a02e15bf97fe8a0b5afc0c4c30`. A CPU-only OrbStack allocation is
requested in #5085. No Docker/OrbStack CLI or container invocation has occurred
for this allocation; until an exact coordinator grant, the formal result is
STOP, not PASS. Repository-wide local CI has not been run because the available
checkout is substantially behind current main.
