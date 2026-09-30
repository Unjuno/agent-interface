# Submit-purpose boundary: preregistered sink-only test

Issue #4373; predecessor #4368; intake main 4a1f3957e91b412a64769199f78f2c4b0102d28b.
This tests an additional application contract. It does not find a production vulnerability,
replace the public runtime, rerun a GUI experiment or rescind the predecessor's ordering PASS.

## H

Equal document revision and content do not identify equal operation purpose. After AUTO stores
revision2/value ab, a distinct SUBMIT with that same revision and value must be able to record
its explicit completion without another document mutation. The exact old sink returns
DUPLICATE_REVISION and records no SUBMIT event. Candidate separates a submissions table from
its document-update log, preserving strict original request fingerprint and revision guards.

## T

Forty fresh cases: ten sequences x two sink policies x two balanced repetitions, in the exact
SCHEDULE.json order. Actor is a real subprocess and owns one new SQLite database per case.
Observer is a second subprocess with URI mode=ro/query_only, after actor termination. Retain
all exact stdin/stdout/stderr, process IDs, argv, outer/inner monotonic brackets, SQL traces,
initial/per-request/final tables and actual database bytes. The source pins and public Git
readback precede the single run.py invocation. Child bound3 seconds; runner bound60 seconds;
externally observed runner exit required. Exclusive output creation; incremental per-case
receipts; zero case retries/replacements/exclusions/pooling/postfreeze changes.

REVISION_ONLY imports the entire unchanged retained sink.py as legacy_sink.py (Git blob
ea30c898c4a26bcd185d62dbcd961d13598620a9). SUBMIT_EVENT adds a new class with explicitly
copied validation/transaction logic and the new event rule. No monkeypatch, stub or source
slice. Source-level comparison is retained. Existing seven-field request schema is unchanged.

Sequences: SUBMIT_FIRST; AUTO_THEN_SUBMIT; SAME_SUBMIT_REPLAY; SAME_REVISION_CONFLICT;
STALE_SUBMIT; CHANGED_REPLAY; KIND_REUSE_ID; BOOLEAN_REVISION; FOREIGN_SESSION;
HIGHER_REVISION_SAME_VALUE. There are92 request evaluations, not92 independent cases.

Excluded construction uses value cd/session unit and temporary files. Twelve unit methods
passed; one separate process-construction packet verifies real sink/observer I/O. These are
not pooled with formal evidence. Source tools and tests do not execute any GUI/model/input.

## D

PASS_SUBMIT_PURPOSE_BOUNDARY_SCOPED requires all40 cases/80 child exits and actual runner
exit; complete unchanged source/packet/SQL/database evidence; zero raw-auditor errors;
twelve effective well-formed copied-record mutation controls rejected without audit crashes.
Legacy records4 explicit submissions; candidate records10. Six additional candidate events
are the AUTO_THEN_SUBMIT, SAME_SUBMIT_REPLAY and CHANGED_REPLAY cases, two repetitions each.
Total document mutations must be identical across arms. Equal-revision SUBMIT must not append
a document commit. All stale/conflicting/invalid/kind-ID-reuse requests must preserve document
state and create no submission event. Same exact job replay creates no second event.
A complete scientific contradiction is FAIL; source/process/denominator/control ambiguity
is HOLD/STOP. No favourable subset, changed threshold or replacement allocation.

The old policy is not called unsafe for its original monotonic-document contract. It simply
does not implement the stronger explicit-Submit event requirement. Caller interpretation
must distinguish DUPLICATE_REVISION from proof of this request's completion.

## C

One trusted epoch/session/document, fixed job identities, serialized SQLite writes, successful
commits, UTF-8 JSON, Python exact int excluding bool, revisions in the original signed64
positive range. DELETE journaling, synchronous FULL, BEGIN IMMEDIATE. No restart/epoch reuse,
multiple editors, rollback of storage history, separate business service or external effect.
SQLite transactions supply the local check/update/event atomic boundary, not cross-service
exactly-once guarantees. A new job ID is a new intent under this narrow contract.

## U

No GUI/public API integration is measured here. The original GUI evidence is separately
preserved in #4368 and cannot be added to this result to claim integrated acceptance.
No performance, token, model, hardware input, population failure-rate, auth or power-loss claim.
Clocks are ordering diagnostics only. No calibrated combined uncertainty u_c or coverage
factor k is applicable to these exact string/counter/record gates; timing uncertainty is
unquantified and not used for a benefit claim. Provided Linux container, not image-attested
Docker/OrbStack. Same-author separate auditor code/process is not external human review.

## Variable / field table

| Symbol or field | Meaning (Japanese) | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| job | 保存要求 | 1 | Original seven-field request | Trusted local JSON | Mapping |
| session, document, epoch | 所有範囲・対象・世代 | 1 | Exact request scope | trial/doc/epoch-1; foreign control explicit | String |
| job_id | 要求の安定識別子 | 1 | Retained request key | Nonempty string, max80 chars | String |
| revision | 文書の版番号 | 1 | Request document generation counter | Positive exact int below signed64 upper bound; no reuse | Integer scalar |
| value | 保存する文書内容 | 1 | Exact requested Unicode string | Max64 chars; fixed ASCII corpus | String |
| kind | 操作目的 | 1 | AUTO or SUBMIT | Equal data need not imply equal purpose | Enumeration |
| fingerprint | 要求内容の整合性値 | 1 | SHA-256 of canonical UTF-8 JSON | Integrity only, not authentication | 256-bit value |
| commits | 文書更新履歴 | 1 | One row per applied document update | Transactionally stored | Relation |
| submissions | 明示確定履歴 | 1 | One row per accepted SUBMIT job | Candidate-only new semantics | Relation |
| ns | 同一ホスト単調時計の標本 | s (stored ns) | time.monotonic_ns | Diagnostic order, not calibrated duration | Integer scalar |
| n | 正式ケース数 | 1 |40 fresh databases | Fixed, no replacements | Integer scalar |

Unit check: revision comparisons and row cardinality compare dimensionless integers. Clock
brackets compare only same-host monotonic nanoseconds; no wall-clock or X11-clock subtraction.
No latency ratios, SI physical limits or statistical confidence intervals are inferred.

## Conditional argument

Initially a new store has revision0 and no submissions. Consider each committed request.
Invalid scope/type, an existing ID with different bytes, stale revision or equal-revision
conflicting value cannot enter an insertion branch. The document-update branch is entered
only by a strictly higher revision. Thus document revision cannot decrease, by induction.
An accepted SUBMIT with equal current revision/value uses SUBMITTED_CURRENT, adding only a
submission row. With a higher revision it updates the document and records the submission
in the same transaction. Both then record the job fingerprint. A later exact same-ID request
is handled before those insertion branches; changed same-ID content conflicts. Therefore a
retained job ID creates at most one submission event under the stated serial transaction
and preserved-store assumptions. Absence of retries at the GUI layer is not asserted.

Counterexample to revision-only completion: AUTO(job A,revision2,ab) changes the document;
SUBMIT(job S,revision2,ab), with S distinct from A, is DUPLICATE_REVISION in the old store.
Its document is correct but commits has no SUBMIT. The added event contract distinguishes
these facts; it is not a claim that old DUPLICATE_REVISION falsely said APPLIED.

## Background / handoff

Primary implementation context: https://www.sqlite.org/lang_transaction.html and Amazon
Builders' Library, Making retries safe with idempotent APIs (client identity versus identical
parameters). Known mechanisms; this is concrete executable contract validation, not novelty.
Applicable areas: GUI result vocabulary, transactional persistence, idempotent message handling.
Adoption requires an application owner to define whether Submit has semantics beyond saving
bytes. Do not silently turn a database event into a business action or input authority.

Roadmap: construction -> public full-source/gate readback -> single formal run -> independent
raw audit/controls -> complete evidence PR -> exact-head applicable CI/scoped review -> allowed
main merge/readback -> only owned dependency-safe cleanup. Global ROADMAP remains incomplete.
