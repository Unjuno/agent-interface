# Historical result projection — Issue #4366

Allocation: result-value-replay-20260925-e5d7-01.
Intake main: 4a1f3957e91b412a64769199f78f2c4b0102d28b.
Owned branch: research/result-value-replay-20260925-e5d7.
Owned path: research/verification/result_value_replay_e5d7_v1/.

## H

At-most-once effects are insufficient for historical-result fidelity. Replaying an
old operation ID with a current value/version can misattribute later effects.
Returning the stored operation result and separate current diagnostics avoids that
projection error. An ABA value return can conceal a wrong commit version.

## T

Two policies, six schedules, two repetitions:24 fresh DB cases and96 separately
executed receiver processes. Four receivers deliberately exit73 AFTER commit and
BEFORE response;92 exit0. Every actor is local and disposable, using JSON stdin
and stdout; no network/model/GUI/input action occurs. SQLite DELETE journal,
synchronous FULL, timeout0, explicit BEGIN IMMEDIATE; effect and original-result
recording share a transaction. Both policies store identical information and
only the replay projection differs. Counter starts0/version0. Requests have
scope e5d7-private and exact operation_id/delta content binding.

Frozen schedules (each final pair is two replay/conflict probes):
- STABLE: A+1,A+1,A+1.
- OTHER_EFFECT: A+1,B+3,A+1,A+1.
- ABA: A+1,B+3,C-3,A+1,A+1.
- LOST_REPLY: A+1 exits73,B+3,A+1,A+1.
- PAYLOAD_CONFLICT: A+1,A+2,A+2.
- NEW_OPERATION: A+1,B+3,D+2,D+2,D+2.

Source/gates must be published and exact Git blobs read back before formal0.
Six immutable batches in the order above, four cases per batch; repetition0 then1,
each CURRENT_PROJECTION then RECORDED_RESULT. Each batch consumes a new directory
using exclusive mkdir and runs once; stop on an incomplete batch. No retry,
replacement, exclusion, pooling, extension or post-result tuning.

Construction:two schedules(STABLE,ABA), one repetition per policy=four cases,
16 receiver processes, plus8 pure unit methods. These records are excluded.
Source parser/argv-portability inspection was corrected before construction;
no construction failure occurred in the two live construction batches.

## D

PASS_HISTORICAL_RESULT_PROJECTION_SCOPED iff all24 cases/96 process receipts,
raw stdout/stderr/request/SQL/DB snapshots/source hashes and expected schedule
reconcile; both policies have0 duplicate effects; fresh/new operations work and
changed payload conflicts; CURRENT_PROJECTION has12 mismatched replay responses
in six cases(8 wrong values,4 ABA version-only); RECORDED_RESULT has0 mismatches;
current diagnostics remain correct; missing first replies stay absent; all
responses authority=false and task_success=null; independent raw-only auditor
errors=[];12 effective copied-evidence controls reject normally. Integrity gaps
are HOLD/STOP, complete contradictions FAIL. Scoped PASS tests this explicit
historical-result contract, not general API behavior or production readiness.

Controls mutate valid evidence copies:result value/version,authority,task success,
new-effect flag,boolean delta,exit,PID,call count,DB value(with refreshed hash),
ABA version and source bytes. They must change actual bytes and return normal
rejection, not crash or no-op. Audit imports neither receiver nor runner.

## C

CURRENT diagnostics can legitimately change; only the explicitly historical
result field must stay bound to the original operation. Entire response byte
identity is NOT required. Both methods store the same result ledger, so no
storage/latency claim follows. Trusted scope, complete retained operation IDs,
cooperative single DB, no outside writer and successful commits are assumptions.
The comparator is authored diagnostic code, not an unchanged-runtime defect.

## U

No GUI/external-effect atomicity, authentication, retention GC, split brain,
power-loss durability, model/token/latency gain, natural failure probability or
cross-platform claim. Same-author separate auditor is not external human review.
Clock values are process diagnostics only; no threshold or statistical uncertainty
is inferred. Calibrated combined uncertainty and coverage factor are unavailable.

## Variable table and unit check

| Field | Meaning (Japanese) | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| operation_id | 意味的な操作識別子 | 1 | Scope-local immutable request key | nonempty str, length1..32 | identifier |
| delta | 私有カウンタへの加算量 | 1 | Applied once for a new ID | exact integer -3..3, bool forbidden | integer scalar |
| counter_after | その操作直後のカウンタ値 | 1 | Cumulative committed deltas at that operation | integer, original effect boundary | integer scalar |
| commit_version | その操作を確定した版番号 | 1 | Increments once per new committed operation | positive integer | integer scalar |
| current.counter/version | 応答時点の値と版 | 1 | Same transaction's current-state read | separate from historical result | integer pair |
| started_ns/ended_ns | 子プロセスの観測時刻 | s(stored ns) | time.monotonic_ns, same host | diagnostic only | integer scalar |

Unit check:counter addition and all acceptance/count/version comparisons are
dimensionless. Nanoseconds are never mixed into result-value comparisons.
Numerical discriminator:A+1 gives(1,1),B+3 gives(4,2),C-3 gives(1,3).
The final numeric value1 agrees with A's result but version3 does not equal1.

## Bounded roadmap / integration

Construction -> public source/gate identity -> six first outcomes -> raw audit
and controls -> complete evidence PR -> applicable exact-head CI/scoped review
-> qualified main readback. Keep global ROADMAP/#331/#24 open. Do not recreate
#4134 or call its fixture PASS MAP01 readiness. For #2789, original-operation
result and current application observation are different response fields.

Primary background:AWS Builders Library, Making retries safe with idempotent APIs;
SQLite official Isolation documentation. Known design principles, not evidence
that this local test passed. No old scientific allocation is repeated.
