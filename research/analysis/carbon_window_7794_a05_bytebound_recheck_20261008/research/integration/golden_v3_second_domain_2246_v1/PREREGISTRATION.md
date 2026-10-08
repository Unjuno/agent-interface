# Golden v3 second-domain transfer — preregistration

Issue: #2492  
Parent: #2246  
Branch: `research/integration/golden-v3-second-domain-2246-v1`

## Hypothesis

The source-pinned golden-v3 adapter and independent effect/cleanup boundary validated on the Tk/Xvfb fixture transfer to a second disposable desktop-like fixture without authority laundering, unsafe replay, or conflating process completion with task success.

## Frozen scope

The only changed factor is the fixture/domain. The adapter route, result vocabulary, receipt lineage, freshness/binding admission, safe-stop policy, and scoring rules remain fixed from current main. This allocation is model-free: provider/model authority, token benefit, and planner behavior are excluded and remain unverified.

## Required case matrix

The second fixture must support a source-pinned, independent scorer for these first-result cases:

1. useful effect;
2. execution unavailable before input;
3. guarded refusal before consequential input;
4. accepted input with no useful effect;
5. partial or collateral effect;
6. stale target invalidation with bounded repair;
7. ambiguous delivery where replay is unsafe;
8. terminal release and cleanup failure.

Each row retains source observation, action/receipt lineage, authority and lease state, input events, effect evidence, cleanup state, lifecycle ordering, and output hashes.

## Formal gate

Run exactly one first-result block in an ephemeral pinned container after the fixture image, runner, auditor, and source blobs are frozen. No rerun, replacement, tuning, or pooling after formal output.

`PASS_GOLDEN_V3_SECOND_DOMAIN_SCOPED` requires:

- all eight case outcomes are independently reconstructed;
- lifecycle field/order identity is preserved;
- authority remains false until independent admission;
- useful, partial, collateral, refused, stale, and unknown outcomes remain distinct;
- stale/ambiguous cases safe-stop without blind replay;
- cleanup failure cannot become task success;
- terminal input is neutral in every case;
- source/result/audit hashes agree.

Any unsafe admission, wrong-target effect, replay after ambiguous delivery, or provenance contradiction is `FAIL_GOLDEN_V3_SECOND_DOMAIN`. A reproducible but unavailable or semantically insufficient fixture is `HOLD_GOLDEN_V3_SECOND_DOMAIN_FIXTURE`.

## Stop and non-claims

Stop after the first PASS/HOLD/FAIL/STOP. Preserve all raw evidence and failed attempts. This does not establish provider-backed model decisions, model tokens, latency benefit, six-task live acceptance, general application coverage, native backend coverage, or human tempo.