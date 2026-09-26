# Producer epoch binding — Issue #3933

Parents #3876, closed #742 and merged research-only reader #3883. Base main:
`b2457b746a6df06f6536585dfe2ab937aff639f4`.
Branch: `research/passive-reader-epoch-binding-20260922-v1`.
Additive scope: this directory only. #3917 owns live producer integration;
#3931 owns host response/cursor crash persistence. Neither is duplicated.

## H — hypothesis

The existing caller-owned stream ID and consumed-prefix digest cannot identify
a new producer lifetime when the consumed prefix is identical. An owner-chosen,
distinct epoch persisted in every DeliveryLedger record and checked before
exposing a reader batch prevents cross-lifetime notification aliasing. This is
an empirical contract boundary already predicted by HOST_CONTRACT.md, not an
undocumented defect discovery. No epoch is inferred from PID/mtime/path.

## T — frozen allocation

Allocation `epoch-formal-20260922-01`, exactly once. Provided Linux x86_64
execution container, CPython 3.13.5. Docker CLI absent; no Docker/OrbStack image
identity or replication claim. No model/provider/network experiment, GUI/OS
input, credentials, package changes or shared runtime edits.

Exact upstream copies:
- reader.py: Git blob ea72c166c2cea511ea91031dfbb14563fe4e3245;
- delivery_ledger_v2.py: Git blob fb50be9d4d821a7836e6a0158c53a983f0f91df5.

Order: repetitions 0,1,2; inside each repetition the following scenario order;
inside each scenario LEGACY_CALLER_ID then IN_BAND_EPOCH. Total 48 fresh cells.
Each cell has a private file and fresh producer/reader subprocesses. First read
consumes exactly two complete records; each subsequent read is a new process.

| Scenario | Initial values | Transition | Last read |
|---|---|---|---|
| APPEND | 1,2 | same producer appends 3 | old epoch/cursor |
| READER_RESTART | 1,2,3 | same file/lifetime | old epoch/cursor |
| RESTART_IDENTICAL | 1,2,3 | new producer replaces with 1,2,3 | old epoch/cursor |
| RESTART_SHARED_PREFIX | 1,2,3 | new producer replaces with 1,2,303 | old epoch/cursor |
| RESTART_CHANGED_PREFIX | 1,2,3 | new producer replaces with 101,2,3 | old epoch/cursor |
| RESTART_SHORT | 1,2,3 | new producer replaces with 1 | old epoch/cursor |
| MIXED_EPOCH_SUFFIX | 1,2 | new producer prepares 1,2 without writing; appends 3 | old epoch/cursor |
| FRESH_EPOCH_ADOPTION | 1,2,3 | new producer replaces with 11,12,13 | new epoch, no cursor |

The two test epochs are case ID + :A and :B. Legacy records omit epoch;
candidate records add producer_epoch before exact DeliveryLedger.prepare.
All records are canonical JSONL. Barriers are pipe command/response order,
not sleeps. Replacement uses os.replace in the private directory. fsync is
performed but no power-loss durability is tested. Producer stdout records
prepared/emitted bytes and file digest. Reader stdout records exact receipt or
typed rejection. Returned candidate batches are all-or-nothing for epoch checks.

The scientific sources, auditor, tests, environment and this plan are fixed by
FREEZE.json, whose digest is posted before formal execution. The runner checks
it before and after the allocation. An outer supervisor has a 240-second bound,
retains exact runner exit/output, then invokes a separate raw-only auditor and
an eight-method test/control process. Evidence mutations affect copies only.
No retries, replacement cells, threshold tuning or pooling of construction.

## D — decision gates

PASS_PRODUCER_EPOCH_BOUNDARY_SCOPED requires every planned cell, exact source,
protocol/transcript/epoch/PID/payload/cursor identity and no-input flags to agree
with the separately implemented raw-only oracle. Legacy must expose aliasing
in all nine identical/shared-prefix/mixed-suffix cells, and reject all six
changed/short prefixes. Candidate must reject all fifteen stale-epoch cells,
with no returned record list or new cursor. Both protocols must resume the
three positive scenarios (18 cells total). All producer and reader exits must
be exact integer zero, with no unaccounted output, and all eight mutations
must be rejected. Exposed receipts remain authority=none, acknowledged=false,
input_dispatched=false. A positive hypothesis verdict does not make the legacy
misuse safe. A candidate mismatch is scientific FAIL; provenance, timeout or
missing/audit evidence is HOLD/STOP. Keep first outcome and all partials.

## C — constraints and interpretation

This is an owner-cooperative finite file/protocol fixture using existing ledger
and reader code, not a new background sensor, inbox, ACK or production emitter.
The candidate adds in-band per-record epoch evidence, not a separately racing
sidecar. Epoch consistency is not producer authenticity. Empty reads attest
neither producer identity nor termination. The read is a snapshot, not authority
for a subsequent action or assurance against later file replacement.

## U — unknowns and roadmap

Persistent production epoch allocation, actual producer/host adoption, terminal
lifecycle, crash/power-loss durability, multi-producer ordering, distributed
exactly-once, ACK/model consumption, useful-feedback timing, GUI correctness and
performance remain open. No production promotion from this experiment.

Reconstruction -> excluded construction -> freeze -> formal48 -> independent
raw-only audit/eight corruption controls -> additive PR -> verified main readback.
Only this allocation may close. #3876 and the full ROADMAP remain open.
