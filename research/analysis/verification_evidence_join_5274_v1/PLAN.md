# Verification evidence reduction: finite first rung for #5274

Allocation: `verification-evidence-5274-20260929-vj01-01`.
Intake main: `4244aaf8b1d0ad2b26d64813842f801ce8f66612`.
Owned branch: `research/verification-evidence-5274-20260929-vj01`.
Only `research/analysis/verification_evidence_join_5274_v1/` is scientific work.
A mechanical generated-index update may be added for applicable repository CI.

## Research roadmap and H/T/D/C/U

Construction -> public source/input/gate freeze and readback -> one finite run ->
separate raw-only audit and corruption controls -> evidence PR -> exact-head
checks/review -> qualified main readback. Global ROADMAP, #5267 and model/live
utility remain open. No old allocation is rerun. Closed #5225 motivates explicit
missing-evidence treatment; it supplies no observations to this experiment.

**H.** In a fixed decision scope, accumulating sets of result payloads and sealing
one evidence cut permits an order-independent final three-way verdict, while
preserving missing/role-incompatible/conflicting evidence. Scalar verdicts are
not monotone: a provisional PASS may become UNCERTAIN when a conflict arrives.

**T.** Two mandatory checks (`target`: CURRENT, `effect`: VERIFIED_EFFECT), one
optional diagnostic (CURRENT). Each of the three slots has eight variants:
absent; expected-role PASS/FAIL/UNKNOWN/TIMEOUT; HISTORICAL PASS; PREDICTED PASS;
or other incompatible role PASS. All 512 assignments and all arrival
permutations give 2,374 schedules. The frozen 22 directed cases add 122
schedules: duplicates, conflicts, identity collisions, scope mismatch, malformed
messages, positive liveness, optional timeout and mandatory veto. Total: 534
cases / 2,496 schedules. Every prefix is recorded. After sealing, two late
messages and another seal must leave the historical result unchanged.
No randomized population sample or model is involved.

Candidate: incremental result-identity/payload sets plus bitset reduction.
Strong simple comparator: separately implemented batch oracle using canonical
JSON grouping and status lists; it imports neither candidate nor runner.
Last-arriving status is an intentionally inadequate negative control, not a
competitive implementation or basis for a speed claim.

**D.** `PASS_FINITE_EVIDENCE_REDUCTION_SCOPED` requires all 2,496 schedules and
all prefixes to match the independent oracle, all 22 hand-declared directed
outcomes, source/input/receipt integrity, no authority, and all 12 effective
raw-row corruption controls rejected. Complete candidate mismatch is FAIL;
source/incomplete/audit failure is HOLD or STOP, never inferred PASS. No
post-outcome changes, retries, exclusions or pooling. One supervised formal
invocation, then one independent audit invocation. Construction may be debugged
separately with preserved outcomes.

**C.** The chosen plan/required checks and role declarations are fixture inputs,
not learned semantics or authenticated truth. Ordinary set reduction may be
entirely sufficient; no learned aggregator is assumed necessary. The seal is
an explicit same-evidence-cut operation, NOT arrival-order independence across
different cuts. No irreversible action uses a provisional verdict.

**U.** Finite synthetic contract only. No real verifier truth, ontology
completeness, calibrated confidence, runtime safety, live effect, model quality,
latency/token saving or production promotion. Same-author independent code is
not independent human review. No probability/coverage factor is estimated from
these exhaustive assignments; statistical standard uncertainty and k are not
applicable. Timing receipts identify execution, not a performance benchmark.

## Frozen precedence and identity contract

1. Message keys are exactly rid/check/subject/session/decision/epoch/role/value.
   All but epoch are nonempty strings of at most 128 characters; epoch is an
   integer, explicitly excluding Boolean. Unknown checks/roles/statuses or bad
   schema create an integrity warning.
2. Session `session-vj01`, decision `decision-vj01`, epoch 7 and subject equal to
   check define this fixture's scope. Foreign scope is rejected and cannot
   satisfy a required check. A foreign record does not poison valid evidence.
3. Equal result ID and identical payload is idempotent. Equal result ID with
   unequal payloads quarantines the WHOLE identity, independent of arrival order.
4. Evidence roles match exactly: VERIFIED_EFFECT is not a synonym for CURRENT.
5. An unopposed mandatory FAIL wins, even if another check has an integrity
   warning or disagreement. A FAIL opposed by PASS on the same check is a
   conflict, not an unopposed failure.
6. Otherwise any integrity warning or same-check PASS/FAIL conflict gives
   UNCERTAIN. Optional conflicts also give UNCERTAIN in this frozen policy.
7. Otherwise PASS requires each mandatory check's valid value set to be exactly
   {PASS}. PASS plus UNKNOWN/TIMEOUT is not sufficient. Optional UNKNOWN,
   TIMEOUT or an unopposed optional FAIL is nonblocking in this fixture.
8. All other states are UNCERTAIN. `seal()` freezes a historical result only.
   Later results increment late count without revising it. Live invalidation or
   revision must open a new externally versioned decision and is NOT implemented
   or authorized here. `authority` is always false.

## Variable / field and unit table

| Symbol/field | Meaning | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| rid | result identity | 1 | bounded nonempty text; groups payload variants | string |
| check / subject | verification target | 1 | target, effect, diagnostic | enum/string |
| session / decision | scope identity | 1 | fixed identifiers above | string |
| epoch | fixture generation | 1 | integer 7, not Boolean | integer scalar |
| role | evidence kind | 1 | CURRENT, VERIFIED_EFFECT, HISTORICAL, PREDICTED | enum |
| value | submitted observation outcome | 1 | PASS, FAIL, UNKNOWN, TIMEOUT | enum |
| P/F/U | reduced verdict | 1 | PASS, FAIL, UNCERTAIN; not numeric ranking | enum |
| start_ns / end_ns | diagnostic process time | s (stored ns) | local CLOCK_MONOTONIC | integer scalar |
| bytes | encoded length | 1 (stored bytes) | nonnegative byte count | integer scalar |

Unit check: only same-clock nanosecond timestamps are ordered. Epochs/counts
are dimensionless and never treated as elapsed time. Role/status/ID values
have no numerical attention weight or probability meaning.

## Execution environment and commands

Provided session-local Linux x86_64 container, CPython 3.13.5, standard library.
No Docker CLI/image claim, shared #5085 resource, GPU, GUI, input, model/provider,
user data or experimental network. No package installation. Unpinned CPU
frequency; no timing comparison. Source and result paths are dedicated.

From this directory:

```sh
python -B -m unittest test_construction -v
python -B experiment.py --run evidence/formal01
python -B audit.py evidence/formal01 --write evidence/AUDIT.json
```

The outer local runner retains exact argv, stdout, stderr, exit codes and
monotonic start/end. Formal has a 30-second timeout and 512 MiB address-space
limit; audit has 30 seconds / 512 MiB. Original raw is never overwritten;
auditor writes separately. A replay is an explicit offline audit, not another
formal scientific allocation.

## Preparation failure retained

Attempt 01 could not resolve raw.githubusercontent.com from this container.
The shell then attempted unittest with source absent and retained
ModuleNotFoundError / exit 1. No formal runner executed. The DNS traceback is
available in the conversation tool result; only the unittest stderr/exit were
saved locally, so full local download stderr is not claimed. Attempt 02 uses
MCP-supplied exact text with four matching Git blob IDs. Its 12 construction
methods passed; this is excluded construction, not the formal matrix result.
