# Issue #1460 — generation ABA v3 first formal outcome

Decision: **PASS_T2_GENERATION_ABA_GUARD_SCOPED**.

One frozen invocation produced 200,000/200,000 deterministic traces. Candidate/oracle mismatches were 0. All 40,000 explicit stale-generation ABA attempts were refused by GENERATION_BOUND_REOPEN, while the STATE_ONLY_REOPEN discriminator produced 40,000 stale effects. All 20,000 fresh g2 CLEAR controls admitted; WATCH/HARD/ordinary-authority=false effects were 0. Audit passed 200,000 rows with errors=[], and 7/7 copied-result corruption controls were rejected.

Formal invocation/reruns/replacements/tuning: 1/0/0/0.

Formal raw SHA-256: `c584f465965c021f46e51b6ce0737e2518c6e8184e6a796105fd0fc93465aaba`.

## Publication state

Full FORMAL.json is retained locally (31,589,431 bytes) and losslessly packed with audit/controls/source/execution receipts into `evidence.tar.xz` (1,066,844 bytes), SHA-256 `d5ada472b7bd7df0ef5b483df2a19f1021f7de6a5e8958bf8d6c4b5ce04a2604`.

This branch records the exact result/audit/control hashes and execution receipts. Full raw byte delivery is **HOLD_RAW_BLOB_TRANSPORT_UNAVAILABLE_IN_CURRENT_CONNECTOR** because the available GitHub write action accepts inline content but has no local-container file upload handle. Do not rerun the consumed allocation to repair publication.

## Scope

Synthetic standard-library state-machine composition only. No physical actuation cancellation, model/provider latency, task usefulness, X11/MAP01, tokens, human tempo or production-runtime claim.
