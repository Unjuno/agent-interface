# Input-owner critical normalization v1 — retained first outcome

Decision: **`PASS_INPUT_OWNER_CRITICAL_NORMALIZATION_SCOPED`**.

One source-first formal invocation, reruns 0. Frozen seed `104220260918001` evaluated **25,000 valid** source-derived records and **10,000 invalid** records.

Results:
- candidate vs independent oracle kind mismatches: **0**;
- invalid records accepted: **0**;
- exact #1021 critical-retention composition errors: **0**;
- raw-provenance preservation errors: **0**;
- normalized critical counts: `FOCUS_CHANGED=3,113`, `LEASE_EXPIRED=3,049`, `AUTHORITY_REVOKED=9,357`, `SAFETY_VIOLATION=9,481`.

The adapter requires caller/transport envelope identity, sequence, received time and scope; it never invents these from the raw input-owner payload. Verified neutral owner release maps to focus/lease/revocation semantics according to the frozen reason table. Unverified or non-neutral release maps only to `SAFETY_VIOLATION`, preventing release-proof laundering. `owner_failed` and `cleanup_failed` map to `SAFETY_VIOLATION`. Ordinary `input_admission`, unknown verified release reasons and malformed envelope/records fail closed.

Every valid normalized record was then passed through the exact #1021 reducer Git blob `404a452aa304b4bde73ec0182450d241e2a744af`; every critical event survived exactly once/in order and output authority remained false.

Independent audit passed with errors `[]`; six corruption controls rejected 6/6. Model/provider/GUI/task-input/authority actions: 0.

Scope: input-owner family only. Observable-signal guard `HARD_INVALIDATED/UNKNOWN`, `ACTION_REJECTED` and semantic `EFFECT_VERIFIED` normalization remain separate. This is a contract/mechanics result, not a live-frequency, model-benefit, X11-physical-truth or production-ABI claim.
