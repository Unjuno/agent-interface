# Issue #5960 T1 retained-cohort eligibility audit

Allocation `R133-RECOVERY-PRESNAPSHOT-5960-T1-ELIGIBILITY-AUDIT-20261002-01`; main source `69a1bf509eb432e5e3c0c294d05ad7671d86adb6`.

## Disposition

**`HOLD_NO_ELIGIBLE_RETAINED_COHORT` in the bounded cited inventory.** Six candidates were inspected; zero satisfy all five frozen T1 gates: case-level pre/post evidence, source clock, independent causal label, eligible safe-slack failure, and diagnosis/reproducer-utility outcome. The inventory is deliberately bounded and is not a claim that no suitable evidence exists on any remote branch or issue.

## Findings

- #615 retains a six-case recovery-handoff summary and source archive. It compares reuse of an already-current post-recovery observation with an extra observe-only program; its result does not retain case-level pre/post volatile evidence plus independent failure-cause labels or diagnostic-utility outcomes.
- #862's Issue record reports an eight-session authored focus-transfer seam and aggregate first outcomes. The main-branch study directory has freeze/preregistration/source code but no case-level result artifact. The focus remains XTerm B across recovery; this tests receipt composition, not recovery erasing a cause-discriminating signal.
- #3991 is a construction STOP after 31 directories; formal experiment never started. Its partial SQLite files are a harness-integrity failure, not an eligible real interface-failure cohort.
- #5430 and #5666 are open proposals without executed cohorts.
- Parent #5960 T0 is synthetic with planted causes, so it is explicitly excluded from empirical T1.

GitHub code-search queries for `pre_recovery observation recovery`, `post_recovery_observation failure cause label`, `REJECT_CONTEXT_CHANGED receipt`, and `recovery diagnosis failure_id` found the #862/#3991-related code but no direct case-level T1 cohort schema. Search coverage is limited to indexed default-branch code. Exact main commit and inspected Git blob IDs are frozen in `FREEZE.json`; individual source links and gate extractions are in `eligibility_inputs.json`.

## Decision / next evidence requirement

Do not reclassify any retained result or spend a consumed live allocation. T1 remains HOLD until an eligible existing cohort is found or a separately authorized prospective comparison can retain source-bound pre/post cases, a monotonic clock, blinded independent cause/effect labels, safety slack/release ordering, capture cost, and post-recovery diagnostic/reproducer scoring. This audit did not run a candidate or interact with a live app.

The initial repository-root test invocation failed before discovery because the test module did not add its package directory to `sys.path`. The bootstrap was fixed and the root-level suite then passed 3/3. No formal eligibility-auditor rerun was made for this harness-only correction.
