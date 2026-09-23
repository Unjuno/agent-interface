# Issue #4027 — outcome-query coverage after receipt retirement

## Decision

**PASS_RETIRED_OUTCOME_COVERAGE_SCOPED**, one prospectively frozen allocation,
three immutable batches, 48 fresh cases, no formal rerun/replacement/exclusion.
The separate raw-only auditor exited 0, errors empty, 12/12 corrupted copies
rejected. This is a research evidence result, not production runtime promotion.

## H / T / D / C / U

**H.** A missing outcome outside retained history cannot distinguish an old
committed effect from a never-accepted request. Checking coverage before treating
absence as permission to retry prevents the selected duplicate/conflicting
effects, while deliberately leaving old never-accepted work unresolved.

**T.** Two fixed clients, LOOKUP_ONLY and COVERAGE_AWARE, receive the same query
contract from a private SQLite application. Only client interpretation of missing
old-epoch outcomes differs. Atomic effect/receipt writes and atomic retirement
are identical. Eight scenarios, three repetitions per client; 177 actual fresh
receiver processes, 48 read-only queries, three separately supervised runners.
Retirement deletes epoch-7 receipts and advances coverage to epoch 8 without
deleting effects. Query cannot inspect effects: SQLite read-only mode and an
authorizer allow only meta/receipt reads; exact SQL and before/after DB bytes
are retained. There is no GUI, model, provider, or experimental network call.

**D.** All frozen decisions, effect counts, identities, packets, SQL, database
bytes, source hashes and process exits reconcile. Every runner returned 0 with
no timeout and empty stderr. All 177 receiver waits returned 0. All recorded
receiver and runner PIDs were absent at the post-run /proc check. This last check
is descriptive for these recorded PIDs, not a general PID-reuse safety proof.

**C.** The receiver deliberately has no retired-epoch submit fence in either
arm. It is a negative-control fixture, NOT a production implementation to deploy.
An independently enforced receiver fence could already stop a naive client.
Known idempotency mechanisms are not claimed novel; #531 already covers scalar
retirement admission. Our different object is the outcome-query's information
coverage and its effect on the declared recovery client's choice.

**U.** Single cooperative owner, serialized SQLite operations, exact known
schema, no concurrent GC/query, crashes, power loss, forged epochs, real GUI
external effects or automatic re-ID/restamping. No model behavior, throughput,
latency, token, population reliability or Docker/OrbStack equivalence claim.
Three repetitions are finite directed checks, not independent population samples.
Same-author independent code/process audit is not external human review.

## Retained outcomes

Each table cell below occurred in all three repetitions. Counters are sums of
private integer deltas, not action counts. Initial effect count is 1 except
RETIRED_NEVER_ACCEPTED, where it is 0.

| Scenario | LOOKUP_ONLY decision | COVERAGE_AWARE decision | Final counter: lookup / aware |
|---|---|---|---:|
| RETAINED_APPLIED | COMPLETED | COMPLETED | 1 / 1 |
| RETIRED_APPLIED | NOT_FOUND_CURRENT; submit | OUTCOME_UNKNOWN_RETIRED | 2 / 1 |
| RETIRED_NEVER_ACCEPTED | NOT_FOUND_CURRENT; submit | OUTCOME_UNKNOWN_RETIRED | 1 / 0 |
| RETIRED_CHANGED_PAYLOAD | NOT_FOUND_CURRENT; submit | OUTCOME_UNKNOWN_RETIRED | 3 / 1 |
| FRESH_NEW_INTENT | NOT_FOUND_CURRENT; submit | NOT_FOUND_CURRENT; submit | 3 / 3 |
| RETAINED_CHANGED_PAYLOAD | CONFLICT_CONTENT | CONFLICT_CONTENT | 1 / 1 |
| WRONG_SESSION | REFUSE_SCOPE | REFUSE_SCOPE | 1 / 1 |
| BOOLEAN_EPOCH | REFUSE_REQUEST | REFUSE_REQUEST | 1 / 1 |

Lookup-only caused **3 same-payload duplicate effects** and **3 changed-payload
old-ID extra effects**; these are distinct failure classes. Coverage-aware added
zero effects in both groups. It also withheld three genuinely never-accepted
old requests. Both clients allowed the three fresh independent epoch-8 intents.
This is not evidence that refusing everything is useful: the fresh controls
remain live, while old unresolved work needs an additional recovery contract.

A query result never dispatches input or grants authority. The runner performs
only the predeclared private-fixture submission when its client returns
NOT_FOUND_CURRENT. Fresh work-B is separately declared new work, never silent
relabeling of unresolved work-A.

## Information boundary, demonstrated rather than inferred from labels

In each repetition and each client, the actual packet for RETIRED_APPLIED is
byte-equivalent under canonical JSON to RETIRED_NEVER_ACCEPTED: same request,
scope, coverage epoch, absent receipt, and neutral authority fields. The
independent database observer nevertheless sees one prior effect versus zero.
Thus any deterministic decision using only those packet fields must give the
same answer in these two histories. It cannot truthfully assert either
"never executed" or "previously completed" in both. UNKNOWN preserves that
information limit; adding an epoch does not recover the missing outcome.

The actual result supports this declared fixture boundary. It does not prove
that arbitrary systems expose a complete or truthful coverage epoch.

## Evidence and integrity

| Artifact | SHA-256 |
|---|---|
| FREEZE.json | 0a1b9c1f4bc26b50c96e9efb15b1b011b296ccfe9f6925d397fafb5facc7eb49 |
| batch-0/RAW.jsonl | 7807905f034868339c118eaff429250ea1b84d25888d45bb5e5e03cf777b5fd4 |
| batch-1/RAW.jsonl | 59c11bca411b3f8d32f40e6908b25e13dcf01f08d530513b4e07e0a680bd70ed |
| batch-2/RAW.jsonl | 79217f1d572b057608661b79307d1998442f4cd28251fbd23b341c10a16247ee |
| AUDIT.json | a57c88b72382d7143493cae9f8c1b28b8ba4b89d6c5ea1e36bfd6fd82dab67f8 |

Each raw row embeds exact database bytes before query, after query and after
recovery, observed table rows, request/response wires, actual SQL and child wait
receipts. Original per-case SQLite and row files remain in the evidence bundle.
All 108 formal files were unchanged by the audit. All nine frozen source hashes
remained exact. Ten policy unittest methods pass both before and after formal.
The auditor imports no runner, receiver or policy; it deserializes retained DB
bytes and independently reconstructs the expected case/command/effect/packet
relations. Finite corruption tests cover missing/duplicate case, Boolean
repetition/exit/request, false DONE/coverage, missing SQL, effect-table query,
query write, foreign PID and a changed DB effect with recomputed hashes. They
are sensitivity checks, not a proof of arbitrary auditor soundness.

The auditor's by_scenario table displays the final repetition's values after
checking every row; it is not an aggregate mean. All three repetitions matched.

## Source-first chronology and retained incidents

Intake main: 1f798cbb60b929e738c6bf8a5912470b38b45ff4. README, CURRENT_GOAL,
ROADMAP, ISSUE_FAILURE_CLASSIFICATION, open/closed lineage, PRs and 118 returned
branch entries were inspected. Closed #24's previous pure status-first result
and #531's watermark source were read, not rerun. Open #331 explicitly excludes
retention expiry. Parallel #3991 and #3998 were not modified.

Issue #4027 was created before construction. One excluded 16-case construction
completed with runner exit 0. Its first auditor incorrectly expected an epoch-7
receipt for a Boolean-epoch query, although SQLite correctly queried epoch 1.
The failed audit and exact earlier auditor remain saved. Only reconstruction
and strict typed comparisons were repaired before formal; read-only re-audit
passed with all 12 controls, without another construction execution. A canonical
formal-output-path guard/runtime-byte checks were added before freeze; the
previous runner is retained. Wrong-path refusal ran before any formal process.

Commit 9376e9e3ddda160fee89c6c6fea13db8b3f61a5d published the exact FREEZE.json
source-hash commitment before formal; remote blob
23254a3169b673295ace7f20500f7998cf1334d6 matched local bytes. Complete source
bytes are delivered with the result, not claimed publicly available before
formal. Issue comment 5767346646 records the preformal command/gates; comment
5767363910 records the first outcome. No frozen source was altered after formal.

The previous chat-local GUI-idle construction remains a distinct
STOP_DUPLICATE_SCOPE, formal 0; its retrospective coordination note is on #3998.
It is not included in this experiment's denominator or evidence archive.

## Environment and limits

Provided Linux x86_64 execution container, CPython 3.13.5 / SQLite 3.46.1,
standard library only. ENVIRONMENT.json retains installed executable/library
hashes and actual platform information. Docker and gh CLIs were absent. No
network calls occur in these scripts; this is not an attestation of enforced
network-none isolation. Clocks are same-container diagnostic monotonic samples,
not timing performance endpoints. No calibrated combined timing uncertainty or
coverage factor is available. Exact dimensionless counters/epochs determine
scientific gates; the field/unit table and dimension check are in PLAN.md.

## Integration handoff / roadmap

The concrete requirement is to expose **status evidence coverage** separately
from **lookup absence**. A retired result cannot be converted to
FAILED_BEFORE_INPUT or permission to replay merely because its receipt is absent.
Keep historical UNKNOWN, current-epoch new-work admission, altered-content
rejection and independent receiver-side replay defense separate. An application
oracle or another explicit recovery contract is needed to recover old liveness.

Completed here: source/lineage check, construction, public freeze, three formal
batches, raw-only audit and finite corruption controls. PR/check/main publication
status is recorded in GitHub discussion, not inferred from local PASS. #2084,
#331, #2789 and global ROADMAP stay open. Do not rerun consumed run.py/supervise.py
formal paths. Any new scientific allocation needs fresh prospective registration;
local publication or harness incidents belong under this same question.
