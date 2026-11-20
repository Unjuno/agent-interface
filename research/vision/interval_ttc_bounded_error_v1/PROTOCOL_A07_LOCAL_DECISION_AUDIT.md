# Issue #8157 A07 retained-raw decision audit

## H / T / D / C / U

**H.** The hash-pinned A02 public, oracle, and candidate files may support a posthoc decision-gate diagnosis even though A02's original auditor failed its reconstruction integrity gate.

**T.** Independently verify frozen raw hashes and the exact A04 `PASS_RAW_RECONCILIATION_ONLY` report hash. Reconstruct every candidate prefix from public history, validate profile/split/hazard and eligibility shape, choose point and interval thresholds from calibration controls only, then compute all original A02 decision components per profile: observed eligible hazard prefixes, numeric intervals, interval containment, invalid-profile terminal false yields, evaluation-control false yields, eligible hazard yields, and paired lead. A06's stopped artifact remains untouched. Do not invoke a candidate/generator, A02-A06 auditor, or any container/runtime.

**D.** A07 can only report `NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW` when exact inputs, reconstruction, structure, mutation controls, containment and coverage pass while strict noise-profile false-yield improvement or eligible hazard usefulness is absent. If all original score gates pass, report `INCREMENTAL_SIGNAL_ON_RETAINED_A02_RAW_UNSCORABLE`; the original formal A02 `FAIL_METHOD` remains unchanged. Any integrity discrepancy yields `AUDIT_INTEGRITY_FAILURE`; otherwise incomplete or contradictory gates yield `MIXED_OR_INCOMPLETE_DIAGNOSTIC`.

**C.** This is an independent posthoc audit of the same finite synthetic sample, not a new sample or a repair of A02's formal disposition. A02's original mismatch and A03/A05/A06 stops remain preserved.

**U.** No inference about real scenes, TTC calibration, GUI/game behavior, control, or safety.

## Freeze and execution

Freeze this protocol, auditor, tests, A02 input hashes, and A04 report hash before the single local stdlib-only auditor invocation. No network, container, runtime, candidate, generator, or earlier auditor is used. A nonzero exit, mismatch, interruption, or stop is retained without retry or source repair under A07. Any later successor requires a new freeze.
