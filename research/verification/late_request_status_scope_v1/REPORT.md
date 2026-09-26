# Issue #4069 — late request identity boundary

## Result

**PASS_LATE_REQUEST_IDENTITY_BOUNDARY_SCOPED**, one prospectively frozen32-case allocation in two immutable16-case batches. Both external batch exits0;32 app and32 relay exits0; raw-only audit errors0;12/12 evidence mutations rejected;10 receiver unit tests pass. Eight frozen source/plan/environment hashes remain unchanged. No formal rerun, replacement, construction pooling or source tuning.

| Receiver key | Cases | Effects | Counter sum | Late duplicate cases | Changed payload accepted | Query count |
|---|---:|---:|---:|---:|---:|---:|
| ATTEMPT_KEY |16|22|24|4|2|16|
| INTENT_KEY |16|16|16|0|0|16|

The two late-arrival conditions each had two repetitions per arm. Their NOT_FOUND queries were true: no effect or receipt existed yet. Both original/retry arrival orders still produced two effects under ATTEMPT_KEY. INTENT_KEY returned DUPLICATE without a second effect. This is evidence about identity scope, not a failure of query truth.

The two changed-payload controls are distinct: ATTEMPT_KEY accepts delta2 after the original delta1, giving two effects and counter3; INTENT_KEY returns CONFLICT and retains counter1. Both policies refuse wrong session and Boolean delta, deduplicate exact same-attempt redelivery, and complete the deliberately dropped-original case once through the one declared retry. Original-before-query completes without retry. Receiver controls intentionally submit their second message regardless of the first query and are not described as autonomous recovery choices.

All32 queries use a read-only connection, select receipt history rather than effects, and preserve DB bytes. Every returned receipt carries input_authority=false and replay_authority=false. Actual fixture submissions are explicitly authorized only by this isolated experiment schedule. The production CLI is not invoked or modified in this experiment.

## Concrete integration decision

Do not infer FAILED_BEFORE_INPUT, cancellation or guaranteed future non-arrival from a negative status lookup. Within a participating application's retained idempotency contract, carry stable semantic intent identity across transport attempts, bind exact parameters, and perform key lookup plus effect/receipt commit together. This is not a blanket instruction to retry GUI operations. Without that application contract, keep unknown outcome and production no-replay semantics.

The receiver key mechanism is established idempotent-API design, not a novelty claim. The residual tested here is the actual separate relay/app process, pipe, SQLite and client composition under selected arrival orders. A known good request ID alone cannot supply application atomicity, retention, authenticity or fresh action authority.

## Provenance and discipline

Intake/preformal main2308b8301d69b7089a2e0636486736ed59b61537. Public preformal FREEZE commit4eac33b35bd66aee294fc8061df9c71b3af68470, Git blob046d8599fdf9ae79907a93f28236e2ace3308ff8, SHA256d43893eeb981b891708bb6317941a44db0bf65a731e5267f91305545d8276a2f. Source hashes were committed before formal; complete source bytes were initially local and published after execution. Issue freeze comment5768721024; first result comment5768728293.

Batch0 RAW SHA2566a0565bfdd1fa9d8a175ba6a85ca28c0a6aeac47df618936e7b667276ecd36d6.
Batch1 RAW SHA256582e32feed61f7c8a9418bcd2a22ccd212df1a15a74d658410da29caa94fefa0.
Audit SHA2560c8ded657dc25356e03d9c5978fc575255b0fcfaaecfbd996e3e1a714c470002.

Provided Linux6.18.44/x86_64 container, CPython3.13.5, SQLite3.46.1, stdlib only; Docker/gh CLI unavailable. No Docker/OrbStack image pin or network-namespace attestation. No experiment network, model/provider, GUI/OS input, user files, install, shared runtime/workflow or previous-result mutation. Fixed barriers, not a measured random network delay. Exact integer/byte/order gates; timestamps are diagnostic, not calibrated performance.

The candidate and independent auditor were written by the same author using separate implementations/processes. This is not external human/agent approval. No repository-wide local suite is claimed. Exact-head CI/review and main readback are separate delivery gates.

## Prior evidence and publication limits

The previous conversation-local42-case state/event and45-case crash studies were restored and audited without rerunning either experiment. Their output bytes match the original audits, and13/12 pure tests pass respectively; see PRIOR_REAUDIT.json and retained re-audit outputs. Their complete original archives remain unchanged conversation attachments. This new capsule retains only their re-audit receipts, NOT the full older archives. Retrospective crash handoff was posted on #3991 (comment5768665124). Earlier unavailable-publication notes were true then and are not rewritten as prior GitHub publication.

Related parallel #3991 (effect/receipt transaction crash scope) and #4027 (retired outcome coverage) remain untouched. This experiment covers neither. Full project ROADMAP and #2789 are not completed by this evidence-only result.

## ERROR CHECK and remaining uncertainty

Denominator32; all64 actors observed terminal; both batch child exits observed; all source pins stable; all corrupted evidence rejected. ATTEMPT_KEY remains FAIL_SEMANTIC_INTENT_SCOPE even though the boundary hypothesis passes. Counts are directed cases, not natural error rates. Neither observed at-most-once local effects nor a successful query establishes distributed exactly-once delivery, retention after expiry, crash/power-loss persistence, external GUI atomicity, multi-owner authenticity, useful model feedback, latency/token benefit or product readiness.

Next non-duplicating integration question: identify an actual application route that exposes a retained, parameter-bound semantic operation key; measure its composed recovery path before allowing a generic planner to retry. No new generic queue/scheduler or production authority was added.
