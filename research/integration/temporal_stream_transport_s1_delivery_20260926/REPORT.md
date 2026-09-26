# Incremental temporal stream transport — retained-data engineering result

**Local outcome: PASS_WITH_VERSIONED_CONTROL_REVIEW.** Not a first-pass frozen-control PASS, not a new X11 result, and not a production/runtime promotion. GitHub publication was not performed in this continuation because the current connector exposes read actions only.

## What was implemented

`stream.py` is a bounded persistent NDJSON adapter around byte-identical `policies.py` and `upstream_monitor.py` from #4220's retained v2 evidence. A caller can send an open record, individual event records, and close. The process emits per-event outcomes without requiring the caller to resend the full history. OS read boundaries do not reset the monitors. End-of-stream is not a source-time event. Historical result and transport completion/error have distinct fields.

The adapter is experimental research code. It is not wired into the public runtime/CLI/MCP and is not advertised as an authenticated, restart-safe or production service.

## Executed fixed verification

| Plane | Actual result |
|---|---|
| Historical inputs |24 original event streams; their epoch/order/tick/label values are unchanged|
| Normal pipe trials |72: each stream at OS read cap1,7,4096 bytes|
| Per-event comparisons |216, all three contract outcomes match both original outputs and a separately coded oracle|
| Typed invalid-input trials |12, all expected explicit error responses and process exit2|
| Normal process exits |72 exit0|
| Batch runner receipts |4 actual wait-status receipts, all exit0; no missing outer receipt in this new test|
| Forced termination / timeout |0 /0|
| Raw audit |errors=[]|
| Unit construction / regression |12 methods pass, including every single split position of a Unicode control|
| New GUI/X11/model/input work |0|
| Transport evaluation reruns |0|

Actual normal read calls, including EOF:10320 at cap1,1512 at cap7,48 at cap4096. Nonempty reads were exactly1 byte in cap1;1–7 bytes in cap7;316–542 bytes in cap4096. These are observed directed segmentation conditions, not natural fragmentation rates or a latency benchmark. The216 prefix comparisons represent repeated transport evaluations of72 historical source events, not216 newly observed events.

Twelve derivative controls:empty input, truncated final line, missing close, duplicate ordinal, foreign epoch, timestamp regression, Boolean timestamp, malformed JSON, duplicate JSON key, overlong line, message after close, duplicate after historical satisfaction. Already emitted historical satisfaction is not erased, but malformed later transport is ERROR rather than CLOSED. Missing close/EOF never synthesizes a source-time heartbeat or expiry.

## Preserved control-checker failure and its narrow correction

The frozen raw auditor rejected all12 evidence mutations without an exception. Its initial effective-change bookkeeping nevertheless reported `FAIL_CONTROLS`: it computed Python object inequality, where replacing integer0 with Boolean false compares equal. The serialized JSON bytes are different, and the original strict exit-type check already rejected this mutation. This was not an escaping mutation or an adapter defect.

`CONTROLS.json` and the frozen auditor remain unchanged. The separately versioned, post-evaluation `audit_control_bytes_v2.py` compares canonical JSON bytes and records before/after hashes. It confirms12/12 actual byte changes and12/12 original rejection messages, with zero auditor exceptions. A true identical deep-copy control is correctly unchanged. `CONTROLS_BYTES_V2.json` retains this review; it is not presented as a preregistered first-pass control result.

All12 pre-evaluation frozen files retain their exact hashes. No adapter process or original X11 allocation was repeated to obtain this review.

## Previous research remains unchanged

The v1 ZIP (95 files) and v2 ZIP (113 files) remain byte-identical. Read-only checks reproduce the v1 full-audit failure, the v1 prefix-audit output, and the v2 successful raw-audit output. The v2 original `EXECUTION.json` remains absent; its **HOLD_OUTER_EXECUTION_RECEIPT_MISSING** is not repaired by this new adapter's complete process receipts. The v1 partial allocation remains3 complete/1 partial/20 unstarted.

A continuation helper initially compared the v2 re-audit output to the preserved empty output of the old failed audit invocation rather than `auditcopy/AUDIT.json`. That comparison failed. Correct-file read-only comparison matched SHA256 `7c60c64b0c12d5514ef86243e4e7f8b02721dab79c2d306375dd480d36dd5680`; no original artifact was changed. The helper incident is retained separately in the retention bundle.

## Environment and scope

Supplied Linux x86_64 execution container, CPython3.13.5 standard library, OS pipes. Exact environment is in ENVIRONMENT.json. No Docker/OrbStack image attestation, installation, external experiment network, model/provider, user desktop or OS task input. Fixed read caps and a finite historical corpus do not establish general reliability, source completeness, causality, useful task effects, token savings or timing benefit. Same-author separate audit implementation/process is not external human review.

This is a concrete implementation/verification rung for #22's incremental notification interface. It neither displaces #2255's live degraded-evidence work nor launches a new wrapper-only research Issue. The framing argument and typed-field/unit table are in PLAN.md.

## Integration handoff

Adopt only the explicit interface design constraints: retain monitor state across messages, preserve source event order/ticks, frame complete records before decoding, distinguish historical outcome from complete transport, and require separate live currentness/action admission. Current #4224 remains Draft. The connector snapshot shows its three existing CI runs succeeded, but CI does not supply its missing source/raw publication or old outer receipt. This continuation made no remote mutation, PR merge or branch deletion. Publish the additive retained evidence and this engineering extension only through a permitted, reviewed write path. Keep all older formal/HOLD classifications intact.
