# Audit-only successor v5 — freeze

Allocation: `MAP01-HELD-OCCUPANCY-AUDIT-V5-20261002-01`
Purpose: independently audit the already-completed v4 candidate outputs only.
The v4 candidate, outputs and raw v38/v39 inputs are immutable; no candidate or
raw event stream will be rerun or changed.

## H / T / D / C / U

**H.** The new raw-only auditor can independently reconstruct each v4 hold
interval and model-wait intersection, including the one cancel/ack race, while
treating omitted false classification fields on normal completed rows as
false-by-default.

**T.** Invoke the auditor exactly once on the fixed v4 candidate outputs and
both raw trace directories. It recomputes from reports/events and checks
source hashes, hold cardinality, input/admission/release timestamps, all bounds,
decision intersections and totals. Candidate invocations=0, raw log mutations=0.

**D.** `PASS_RAW_AUDIT_V4_OUTPUTS_SCOPED` only if both traces reconcile with
zero errors, all 11 v38 and 29 v39 started holds appear once, one v39
cancel/ack race is independently bound to `Down` only and `[0, 13.209 ms]`,
and all reported intervals and wait intersections exactly match recomputation.

**C.** This audit shares the event schema and scientific assumptions (not the
candidate implementation); source identity and timestamp ordering are checked
directly. The one-window result remains censored, not exact.

**U.** Audits two retained live attempts only. It cannot infer actual normal
key-up times, app-level semantic effect, or general control efficacy.

## Frozen code and inputs

| File | SHA-256 |
|---|---|
| auditor `research/doom/audit_map01_held_input_occupancy_fulltrace_v5.py` | `0f444e45e8777bc8f76908e6c0ce27cf72c2d0ab760287e0613f7623cc60d9ce` |
| auditor construction tests `research/doom/test_map01_held_input_occupancy_audit_v5.py` | `ab92b18227b9a7c47e09b4f167acde42609ced40a470a8b4a7525c5a48a4e1f9` |
| v38 candidate output | `2aeec615483a754233c5b9d483be001952e7ca6cd66370bd1e90bf0389427eee` |
| v39 candidate output | `1cd61f82a2ff832131be4a448bc90663f01c4acaab278807a969d2ef24a3b889` |

Both v5 auditor construction tests pass (2/2); Python byte compilation and
`git diff --check` pass. Outputs are written once to `audit-v5.json`; it must
not already exist at invocation.

No container was started: this is deterministic read-only auditing, and the
shared Docker engine has an unrelated running container with no assigned
exclusive lane. The v4 candidate's host-only limitation is unchanged.
