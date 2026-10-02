# Issue #5960 T0 result — bounded pre-recovery snapshot construction

Allocation `R133-RECOVERY-PRESNAPSHOT-5960-T0-20261002-01`; source main `69a1bf509eb432e5e3c0c294d05ad7671d86adb6`.

## Disposition

**`PASS_METHOD_SCOPED` — synthetic finite-state construction only.** Nine construction tests passed. The candidate ran once over 864 rows (9 planted scenarios × 3 policies × 32 seeds); the separate raw-trace auditor ran once and reported zero errors. No retries.

## Observed in the construction

- For planted causes A and B, normal recovery erases the transient signal. `IMMEDIATE_RECOVER` therefore has no discriminating signal; eligible `PRE_RECOVERY_MINIMAL_CAPTURE` retains the source-bound signal. The null-cause fixture produces no diagnosis.
- Hazard/held-input, zero-slack, and privacy-forbidden scenarios take `safe_release_or_stop` first, record `SNAPSHOT_SKIPPED_SAFETY`, and retain no snapshot.
- Stale-source, missing-receipt, and observer-perturbation controls perform immediate recovery with no snapshot and no evidence promotion.
- The `CAPTURE_EVERYTHING` negative control is explicitly overbroad: it includes a synthetic forbidden payload and costs 9 abstract units against 2 units of slack, so it misses the constructed deadline. Minimal capture costs 1 unit. These are design units, not measured time or privacy risk.

The auditor independently checks 864 trace rows, policy ordering, source/failure binding, no-authority snapshots, unsafe/forbidden skip behavior, hold-to-immediate-recovery behavior, null-cause non-promotion, planted A/B contrast, and budget accounting. Two mutation tests confirm it rejects capture before a safety gate and a forged null-cause diagnosis.

The first invocation from repository root failed during test import because the test module did not add its package directory to `sys.path`; no test was discovered and no formal candidate/auditor ran in that attempt. The test bootstrap was fixed, then the root-level invocation passed 9/9. This harness failure and correction are retained rather than omitted.

## Limitations and next empirical gate

The simulator encodes the causal contrast by construction. This PASS is not evidence that pre-recovery capture improves real diagnostic accuracy, reproducer yield, recovery quality, or operational safety. It measures no runtime latency, observer perturbation, human tempo, or real privacy exposure; its cause labels are planted. T1 remains HOLD until an eligible retained failure cohort with independent cause/effect labels exists, or a future isolated/matched prospective fixture is explicitly allocated with blinded scoring and randomized/counterbalanced policy order. No live shared runtime was used or allocated.

Docker was the preferred execution environment, but Docker Engine did not answer repeated `docker version` requests and was not disturbed or restarted. A small Dockerfile is retained for later exact environment reproduction. The completed local run used host CPython 3.12; container reproduction remains unverified.
