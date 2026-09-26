# Issue 3938 — atomic publication is not a multi-lookup snapshot

## Status

Local scientific result: **PASS_GENERATION_LOOKUP_BOUNDARY_SCOPED**.
Publication gate: **HOLD_RAW_PUBLICATION_INCOMPLETE**. Do not merge this
branch or close #3938 until exact raw evidence is retained on GitHub and
read-back hashes match. The full original evidence is retained in the
conversation archive `agent-interface-issue3938-evidence.zip`.

The local result is not being withdrawn or expanded. The missing GitHub raw
publication prevents another worker from auditing this PR from GitHub alone.
A hash or summary is not a replacement for raw evidence.

## Result

One preregistered formal orchestration completed all 45 cases without retry.
A separate raw-only audit accepted all cases, returned zero errors, and
rejected all nine evidence-corruption controls. All 90 reader/publisher
subprocesses exited zero; formal and audit parent exit codes were zero and
stderr was empty.

| Policy | Cases | Accepted | Refused | Cross-generation attribution |
|---|---:|---:|---:|---:|
| CALLER_ID_ONLY | 15 | 15 | 0 | 6 |
| SIDECAR_PRECHECK | 15 | 12 | 3 | 3 |
| PIN_ONCE | 15 | 12 | 3 | 0 |

These are deliberately exposed cases, not estimates of a random failure
probability. The overall hypothesis PASS does not qualify either unsafe
control as a safe publication policy.

CALLER_ID_ONLY attributed B suffix bytes to the saved A identity in all
three before-prepare and all three between-check/read cases. The sidecar
precheck rejected a B epoch already present before preparation, but in all
three between-check/read cases it checked A metadata and then read B bytes.
PIN_ONCE rejected the three already-switched cases and returned coherent
retained A notifications across the between/after switches. Stable A and
explicit fresh-B adoption controls passed for every policy.

## Why this matters

An atomically replaced CURRENT symlink can point to a fully formed new
generation while still allowing two independent path lookups to observe
different generations. A consumed-prefix digest does not identify the
producer lifetime when the consumed prefix bytes are identical.

The scoped candidate resolves CURRENT once and uses the same retained,
immutable directory for metadata and payload reads. This is a host
publication-contract result, not an undocumented defect in the unchanged
reader and not a new operating-system atomicity theorem.

An A notification returned after B publication can be coherent historical
evidence. It is not necessarily the latest state, fresh target authority,
permission to issue input, an ACK, or proof of model consumption.

## Frozen allocation and provenance

Issue: #3938; parent #3876. Intake main:
`b2457b746a6df06f6536585dfe2ab937aff639f4`.
Allocation: `formal-epoch-publish-7f31-01`.
Freeze was posted before formal execution in Issue #3938 comment 5766184883.
FREEZE.json SHA-256:
`019d94036b94b59844d582c73e5485d94e0cd64a339a2bc59ac78611ffe1ebc0`.

The exact upstream reader and DeliveryLedger Git blobs were verified before
use. The four published source/plan/freeze blobs also match the local frozen
originals. See FREEZE.json and PUBLICATION_STOP.md.

The immutable original raw JSON is 288,509 bytes, SHA-256:
`eef12b6de49f12f34cc86dca0dcea0d66986ed739d9cfc3adf640c966b6a403a`.
Exact original AUDIT.json SHA-256:
`b1625376ee177f8654f6053d8768117f4fcafe6169eefa5e62da9cec9dbe3766`.
AUDIT_SUMMARY.json is explicitly a derived summary, not the full auditor output.

## Environment and construction

Provided Linux x86_64 execution container, CPython 3.13.5; no Docker CLI.
This is not Docker Desktop or OrbStack replication. No GUI, OS input, model,
provider, or experiment network calls occurred. Separate foreground
reader/publisher subprocesses used bounded pipe barriers and actual symlink
replacement over private immutable-generation fixtures prepared by the
existing DeliveryLedger.

Construction-01 reached the enclosing tool's 45-second timeout after nine
complete cases and a tenth partial case. No formal allocation had begun.
Worker invocation was changed to `-S -B` before freeze to avoid unnecessary
Python site initialization. Construction-02 completed all 15 distinct cells
and its separate audit rejected 9/9 corruption controls. Both construction
outputs, including the incomplete first attempt, remain in the archive.
The initial pre-edit runner snapshot was not separately saved; the final
frozen runner is saved. No formal source or gate was changed after freeze.

## Independent audit meaning

The auditor is separate code executed in a separate process. It imports
neither runner, candidate, nor upstream reader and reconstructs identities,
payloads, cursor prefix hashes, ordering, source receipts, process exits and
authority flags from raw evidence. It was written by the same assistant;
this is not an independent human or external replication claim.

## Integration handoff and remaining roadmap

All changes are additive under this issue's namespace. Closed #717's FIFO
restart results are unchanged. #3931 owns host response/cursor crash
persistence, #3933 owns in-band producer epochs, and #3917 owns the live
producer rung. No experiment here duplicates those allocations.

Completed locally: source verification, excluded construction, preregistered
freeze, one 45-case experiment, and raw-only audit with corruption controls.
Blocked: exact raw publication, GitHub-only independent review and main
integration. Existing branches are not deleted: this branch contains unique
unmerged evidence and other branches have separate owners/dependencies.

The next admission condition for this PR is exact-byte raw publication and
read-back verification, not a new formal run. For later runtime adoption,
validate an actual production host/producer pair, define immutable-generation
retention/reclamation, and preserve current-action admission independently.
No production module is changed or promoted. #3876 and ROADMAP.md remain open.
