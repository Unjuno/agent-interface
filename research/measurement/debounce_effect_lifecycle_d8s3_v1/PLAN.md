# Debounced task-effect lifecycle: local prospective protocol

## Research question and lineage
Related GitHub #34 and closed #4134; preserves conversation-local m2q7 without rerun.
New applicability boundary: callbacks are NOT independent. The application coalesces pending writes, so an acknowledged native request can be superseded before a per-request snapshot is written. This is not #4368 arrival-order storage or #4373 equal-revision Submit semantics. No existing runtime defect is alleged.

## H
Current cumulative saved value and a normal cancellation return cannot establish each individually requested snapshot's history. Explicit accepted/scheduled/retired/committed lineage should distinguish WRITTEN, SUPERSEDED_BEFORE_WRITE, CANCELED_BEFORE_WRITE and UNKNOWN. Cancel after commit must not erase the observed write.

## T
Six conditions x two fresh repetitions = 12 private authenticated TCP-disabled Xvfb/Tk sessions. Each F8 increments staged value and schedules a captured-origin write after 400 ms, replacing a pending prior timer. Escape requests cancellation. SINGLE; SERIAL (await first commit before second F8); BURST (second F8 after first receipt but before first timer); CANCEL_PENDING; CANCEL_AFTER_COMMIT; EVIDENCE_GAP (BURST with the first retirement receipt withheld only from reporters). At most two F8 and one Escape; no native re-press/retry. Each F8 is individually acknowledged before the next dispatch; no other task writer. A 450 ms settled observation follows, not a performance metric. Native data are collected once; three shadow reporting policies see the same selected receipts and cannot dispatch. Exactly 12 GUI trials, not 36.

CUMULATIVE_VALUE treats final saved >= requested value as snapshot-write proof. CANCEL_RETURN treats a successful cancellation return as proof of no write; otherwise it uses matching commits. LIFECYCLE requires exact origin+value commit or an explicit pending-timer retirement. These are intentionally limited comparators, not strongest possible alternatives or deployed behavior.

## D
Complete12/source/process/native/app/file/raw accounting. Expected per repetition:9 F8 requests,2 Escape requests,6 persisted writes,3 timer retirements. CUMULATIVE_VALUE must falsely certify the first BURST/GAP snapshot; CANCEL_RETURN must falsely cancel the already committed request. Candidate must report12 WRITTEN,2 SUPERSEDED_BEFORE_WRITE,2 CANCELED_BEFORE_WRITE,2 UNKNOWN over18 requests; zero false written/canceled. Every expected intermediate SERIAL write remains recorded despite final value2. All source hashes unchanged, all owned processes ended, neutral input, separate raw-only audit errors0 and >=10 effective well-formed mutations rejected. Complete contradiction FAIL; missing execution/coverage/control evidence HOLD/STOP. No hidden retries, replacements or postfreeze gate tuning. This is locally frozen evaluation, NOT public preregistration; GitHub publication is a separate pending gate.

## C
Cooperative declared single-thread app; exact ordinary Tcl timer behavior and successful local file writes, no other sender, no event loss before dispatch acknowledgement, no nested update/reentrant callback. Explicit app lifecycle receipts are additional information/cost. Native sender/app association is by one outstanding acknowledged F8 boundary, not keysym equality or arbitrary timestamp inference. Final cumulative state may legitimately satisfy a weaker application task; it does not meet this stronger per-snapshot-write contract.

## U
No crash, power-loss, external service durability, malicious receipts, same-key concurrent senders, natural race rate, arbitrary GUI, model/token/latency benefit or runtime promotion. Monotonic times are diagnostic with no calibrated combined uncertainty or coverage factor. X server neutral is logical state, not physical HID. Same-author separately coded auditor is not external review.

## Roadmap
Pinned source/ownership -> disjoint construction -> local exact source/gate freeze -> two one-shot six-case batches -> raw audit/mutations -> complete evidence, Issue/PR drafts and additive patch -> permitted GitHub publication -> exact-head review/CI -> qualified main integration/readback. Remote write tools are absent; do not claim Issue, branch or PR creation. Global ROADMAP remains incomplete.
