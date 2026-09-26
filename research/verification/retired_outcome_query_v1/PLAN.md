# Issue #4027 — outcome-query coverage after receipt retirement

## H / D
A null outcome record within complete current-epoch coverage can mean not accepted.
The same null record outside retained coverage is compatible with a past effect.
The coverage-aware client must return OUTCOME_UNKNOWN_RETIRED, not completion or
not-found/retry. This sacrifices progress for a genuinely unsubmitted old request.
A newly authorized independent current-epoch intent must remain usable.

The scientific variable is only client interpretation of the same query contract.
Both clients share the exact receiver with atomic effect/receipt writes and
atomic retirement. The receiver deliberately lacks a retired-epoch execution
fence. A production receiver could already have that extra defense; this fixture
is not evidence of a production defect and is not an implementation to deploy.

## T — fixed source-first allocation
Allocation: retired-outcome-coverage-4027-20260922-01. Three serial formal batches,
each16 fresh stores/process chains: 8 scenarios x2 clients. Batch0/2 arm order
LOOKUP_ONLY then COVERAGE_AWARE; batch1 reverses it. Three repetitions total48.
Each command starts a fresh receiver process. No concurrent writer, sleep-based
race, natural timing estimate, model call or GUI input. Integer counter effects
are private SQLite rows. Query uses SQLite read-only mode plus an authorizer
restricting it to meta and receipts; no effect-table access. All writes use
DELETE journal and synchronous FULL. Effect and receipt share one transaction.

| Scenario | Initial effect | Retire epoch7 to8 | Requested work | Lookup-only / coverage-aware | Final counters |
|---|---:|---|---|---|---|
| RETAINED_APPLIED |1|no|original|COMPLETED / COMPLETED|1 /1|
| RETIRED_APPLIED |1|yes|original|NOT_FOUND_CURRENT / OUTCOME_UNKNOWN_RETIRED|2 /1|
| RETIRED_NEVER_ACCEPTED |0|yes|original|NOT_FOUND_CURRENT / OUTCOME_UNKNOWN_RETIRED|1 /0|
| RETIRED_CHANGED_PAYLOAD |1|yes|same ID,delta2|NOT_FOUND_CURRENT / OUTCOME_UNKNOWN_RETIRED|3 /1|
| FRESH_NEW_INTENT |1|yes|new work-B,epoch8,delta2|NOT_FOUND_CURRENT / NOT_FOUND_CURRENT|3 /3|
| RETAINED_CHANGED_PAYLOAD |1|no|same ID,delta2|CONFLICT_CONTENT / CONFLICT_CONTENT|1 /1|
| WRONG_SESSION |1|no|foreign session|REFUSE_SCOPE / REFUSE_SCOPE|1 /1|
| BOOLEAN_EPOCH |1|no|JSON true epoch|REFUSE_REQUEST / REFUSE_REQUEST|1 /1|

Submission occurs only for NOT_FOUND_CURRENT; it is a frozen fixture action, not
an authorization granted by the query. No automatic request re-ID or restamping.
Fresh work-B is distinct semantic work. Each status query must leave exact DB
bytes unchanged, preserve source/identity, and its actual SQL trace must access
only meta and receipts. Raw DB bytes are scored independently of policy labels.

PASS_RETIRED_OUTCOME_COVERAGE_SCOPED requires48 complete cases, all3 actual runner
exit receipts, expected decisions/effect rows above, exact query-packet equality
for retired applied versus retired never-accepted histories, unchanged query DB
bytes, all source/trace identities, raw-only audit and12 rejection controls.
Lookup-only contributes3 duplicate same-payload effects plus3 conflicting old-ID
extra effects. Candidate must add0 in both groups; it conservatively delays3
never-submitted old requests. Report these separately, not as population rates.
Any complete gate miss is FAIL. Missing source, data, process or audit evidence is
STOP/HOLD. No formal retry, replacement, exclusion, pooling or post-result tuning.

Construction: one16-case subprocess matrix, excluded. Its first raw-only audit
had a Boolean-epoch oracle defect; the original source/output are preserved.
Read-only v2 audit corrects the SQL lookup projection; no construction rerun.
Formal output path guard/runtime-hash checks added before freeze; they do not
alter client or receiver semantics. Per-child wait3s, runner supervisor35s,
outer tool envelope45s. These are operational limits, not hard realtime bounds.
Missing/failed prior batch prevents next batch. Existing launch/output refuses.

## Field / variable table
| Field | Meaning | SI unit | Definition / range / assumptions | Type |
|---|---|---|---|---|
| request.epoch | 要求が属する受付世代 |1|positive exact integer below2^63; Boolean invalid|integer scalar|
| coverage_epoch | 記録が完全に保持される現行世代 |1|owner advances7 to8 atomically with deleting old receipts|integer scalar|
| op_id | 一件の意味的操作の識別子 |not applicable|work-A or distinct work-B; never silently replaced|string|
| delta | 私有カウンターへの加算量 |1|integer1..9; experiment uses1 and2|integer scalar|
| effects | 実際にcommitした加算の列 |1 per event|SQLite rows, independently reconstructed; not provided to query|ordered table|
| start_ns/end_ns | 観測処理の単調時刻 |s|stored integer nanoseconds, same container, diagnostic only|integer scalar|
| repetitions | 各条件の反復数 |1|three formal, one excluded construction; not IID population samples|integer scalar|

Unit check: epoch comparisons and effect counts are dimensionless. Counters sum
dimensionless deltas. Stored nanoseconds describe ordered calls only; no timing
threshold is used for scientific acceptance or mixed with an epoch number.

## C / U / bounded roadmap
Cooperative single owner, honest coverage metadata, serialized SQLite, no crash,
power loss, concurrent GC/query, arbitrary issuer rotation, authentication,
receiver defense-in-depth, GUI/model usefulness or actual token/latency benefit.
Known idempotency limitations, not a novel theorem. #531's retirement-admission
mechanism is not rerun or claimed new; this status/effect experiment uses a new
fixture because its contract differs from #531's strict sequential transitions.
No calibrated timing uncertainty or coverage factor is available or invented.

Intake base1f798cbb60b929e738c6bf8a5912470b38b45ff4; closed #24 and open#331,
known #531, current README/CURRENT_GOAL/ROADMAP/ISSUE_FAILURE_CLASSIFICATION,
open/closed Issues/PRs and118 branch entries inspected. Other workers preserved.
Path research/verification/retired_outcome_query_v1/ only.

Roadmap: intake -> construction -> public freeze -> three batches -> raw-only
audit/mutations -> evidence-only PR -> exact head checks/main readback -> own
branch cleanup only with dependency evidence and supported tool. Broad#2084,
#331,#2789 and global ROADMAP stay open. Local incidents stay in#4027.

Primary references:
- https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
- https://www.sqlite.org/lang_transaction.html
- https://github.com/Unjuno/agent-interface/issues/24
- https://github.com/Unjuno/agent-interface/issues/531
