# Issue #5922 T0 — accessibility configuration effect invariance

**Disposition: `HOLD_FORMAL_RUN_INVALIDATED`. Construction passes, but no valid formal audit outcome is claimed.**

## Frozen experiment and construction results

A deterministic synthetic fixture pairs eight declared configurations with three routes (24 rows). It covers default control, 200% text/reflow, stale-coordinate decoy including destructive target, high contrast, reduced motion with/without a completion receipt, app functionality removed by a setting, and a stale accessibility-tree epoch. The frozen candidate does not issue real input; its actions are data records.

Construction suite: 7/7 passed. The independent-oracle design checks exact target/value, authority, release, receipt and declared UNKNOWN state, and has three output-only mutation controls.

## Formal allocation trace — preserved failure

- Source freeze: `5cd7cce871a99e1b1e52dc6356f7f1fe1be8cc09`; parent main `ee0bf5670c4f9cec0c1de1a0e966eb3dd6566c15`.
- The frozen candidate was first invoked once and exited 0, but its exact stdout was not tee'd to a retained output file.
- The independent auditor was then invoked and stopped with `FileNotFoundError: candidate_output.json` (exit 1). This is a consumed, failed audit attempt and is not relabeled.
- In an effort to recover, the candidate was mistakenly invoked a second time. Its output has been retained as `candidate_output_invalidated.json` (SHA-256 `34811e3f8fd3470e6ac8e1cc3edb3b5ba3e433b4256d8f6d3ed2d15cc31f21e6`), but is explicitly invalidated because it is a rerun after the failed allocation. The auditor was not rerun.
- No further candidate or auditor invocation is authorized under this Issue allocation. A future run needs a distinct successor allocation/Issue and must pipe stdout directly to durable storage on the first invocation.

## Docker / environment

Docker Desktop service/processes were present, but the shared Docker inventory was unresponsive/unverified, no Issue-specific lease was assigned, and another task owned a bounded isolated OrbStack slot. This no-external-effect Python fixture therefore ran on host CPU; no engine/container was inspected, started or changed. This is a documented exception, not a container result.

## Scope and limits

This is only synthetic logic under stipulated geometry, colors, accessibility-tree metadata and receipts. No browser/desktop renderer, real preference, WCAG conformance, assistive technology, human participant, production route or model was tested. Do not infer actual accessibility support or user benefit. T1 remains unstarted. The failed allocation and invalidated rerun remain immutable historical evidence.