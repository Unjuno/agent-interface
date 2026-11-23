# Issue #57 late-usage port — rechecked after current-main advance

## Candidate change

Ports late same-turn App Server usage retention from PR #10218 plus a post-score adapter that joins hash-bound sidecars to the existing provider-attempt ledger. This remains an enabling research adapter; it does not automatically call `observe_late_usage` from every runner.

## Current-main identity

The candidate is rebased onto `main` `551cf28bb3ef3249af66d4c1ea33c2ca0b98882e`. Its only rebase conflict was additive `.gitattributes` custody rules; both R281 and task-ledger evidence rules were retained. The runtime tree is unchanged between `381a21a` and `551cf28`.

## Verification

The four directly changed App Server/late-usage test modules pass normally and under `-O` on CPython 3.11.9. `py_compile` passes on all 12 changed Python files. The full 107-test discovery was also run on current main but is **not green**: two Calc/Fake X composition cases failed (stable-menu-anchor error; Save boundary/cancellation terminal timeout), and the test process tree then remained blocked in cleanup until the exact test PIDs were stopped. The full raw failure is retained in `full-normal-current-main.log`; no pass is claimed. Full 107/107 normal and optimized logs on prior base `381a21a` are preserved under `base_main_381a21a/`.

## Evidence custody

The two transferred historical manifests cover 25 files. One missing CR in the original sidecar command file was uniquely recovered at byte offset 737 from its expected SHA-256 and recorded additively; the original PR #10218 head was not altered.

## Limits and disposition

Evidence is deterministic App Server/spool/Fake X with synthetic provider streams. It does not prove real provider delivery/billing, integrated efficiency, GUI effects, MAP01 success, or recovery reliability. The four directly changed modules pass on current main, but the full suite failure needs reconciliation before integration. Keep the PR open and draft while tracing the two existing Calc/Fake X failures; do not relabel the full suite as pass.

## Post-`551cf28` focused recheck (2026-11-21)

Current main later advanced to `8207849ad0bd30b6b31ef4a9cee7eb95f5b4619a`, including changes to the late-usage modules and tests. A fresh four-module run found R01 normal-mode start-receipt timeout plus a publisher-thread cleanup race; `-O` passed. R02 passed both modes but is excluded because its freeze lost the source-hash map. A narrowly scoped test-fixture repair then passed R03 at 26/26 normal and 26/26 optimized, with exact hashes retained in [the recheck packet](../current_main_recheck_8207849_20261121/RESULT.md). The full 107-test Calc/Fake X failures in the prior audit remain unresolved; this focused test repair does not make PR #10218 merge-ready or establish live-provider economics.

## PR #10218 disposition (2026-11-20)

PR #10218 was closed unmerged as superseded after a frozen-main comparison of all 41 changed paths: 37 blobs were identical and the remaining differences contained no unique implementation/evidence to transfer. The late-usage port was transferred to merged PR #10352 and the scheduling/cleanup repair to merged PR #10365; the original source branch remains preserved. See the [path-by-path audit](../pr10218_supersession_audit_20261121/RESULT.md). This historical disposition does not establish real-provider usage or integrated economics; Issue #57 remains open.
