# Issue 3938 — generation publication and repeated lookup

Intake main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Preregistered issue: https://github.com/Unjuno/agent-interface/issues/3938

## H
Atomic CURRENT symlink replacement does not make separately resolved metadata
and payload paths a single-generation snapshot. A once-resolved directory
avoids cross-generation attribution provided generation directories are
immutable and retained. Historical coherent notifications are allowed; this
is not a latest-at-return or input-authority contract.

## T
Use exact upstream reader and DeliveryLedger blobs recorded in FREEZE.json.
Two explicitly named generations A/B each contain three real DeliveryLedger
prepared records. First two encoded records match; the final payload differs.
Initial A read consumes one record. Compare CALLER_ID_ONLY, SIDECAR_PRECHECK,
and PIN_ONCE under STABLE_A, SWITCH_BEFORE_PREPARE,
SWITCH_BETWEEN_CHECK_AND_READ, SWITCH_AFTER_READ_BEFORE_RETURN,
and FRESH_B_CURSOR (explicit B identity and no old cursor).
Three repetitions per cell: 45 fresh cases, one formal orchestration.
Reader and publisher are separate exec'd Python processes. JSON pipe
barriers, not sleep durations, control one atomic symlink replacement.
Every expected process exits zero; timeout/nonzero/missing evidence stops the
allocation and preserves partials. No same-ID rerun or replacement.

## D
All exact cases, bytes, hashes, cursors, process identities, exits and barrier
orders must reconcile in a separate raw-only auditor. Caller-only must alias
B under A in before/between (6 cases). Sidecar-precheck must refuse before
(3), but alias between (3). Pin-once must refuse before (3), return retained
A for between/after, and have zero cross-generation cases. All stable A and
fresh B controls must pass. Exposed receipts keep authority=none,
acknowledged=false and input_dispatched=false. Nine evidence corruption
controls must reject. Gate miss is FAIL; infrastructure/provenance/audit
ambiguity is STOP/HOLD. A hypothesis PASS does not make unsafe controls safe.

## C
Provided Linux x86_64 execution container; Python 3.13.5. No Docker CLI is
available, so no Docker Desktop/OrbStack replication is claimed. The
experiment makes no network/model/GUI/input calls. A finite foreground setup
prepares records; no background sensor or production queue is added.
Single trusted publisher and retained immutable generation paths are assumed.
Path names are not authentication; epoch values are explicit owner metadata.
No in-band epoch field, host cursor persistence or ACK is implemented.

## U
No arbitrary directory deletion/reuse, generation reclamation, hostile
producer, multiple publishers, process/power-loss durability, latest-at-return
semantics, model consumption, latency benefit or production promotion.
#3876 and the full ROADMAP remain open. #3931 owns host crash persistence;
#3933 owns in-band epoch binding; #3917 owns the live producer rung.
Closed #717's FIFO persistence evidence is preserved and not repeated.

## Analytical reduction and residual
If lookup 1 observes generation A, publication switches CURRENT to B, and
lookup 2 follows CURRENT afresh, metadata and payload refer to different
lifetimes. Identical consumed bytes make a prefix digest non-discriminating.
Holding one resolved immutable directory makes both lookups refer to A even
if CURRENT subsequently changes. The experiment tests the actual OS
publication, process-boundary schedule and exact upstream parser interaction;
it estimates no random race probability and is not a novel rename theorem.
Python's primary API references: https://docs.python.org/3.13/library/os.html#os.replace
and https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.resolve .

## Bounded roadmap
Source verification -> excluded construction -> source/gate freeze -> one
45-case allocation -> raw-only audit/corruption controls -> additive PR ->
main readback. Branch deletion requires merged provenance and no dependencies.

## Reproduction
From a repository checkout with the frozen source identities, use Python's
standard library only:

    python -S -B research/integration/inbox_epoch_publication_7f31_v1/run.py formal /tmp/NEW-unique-allocation
    python -S -B research/integration/inbox_epoch_publication_7f31_v1/audit.py /tmp/NEW-unique-allocation/raw.json

A fresh run is a new replication, never replacement of the retained first run.
The auditor can read retained `RAW.json.gz.b64` directly; it does not import
the runner, upstream reader or candidate policy. Audit independence means
separate code/process and raw reconstruction, not a separate human author.

## Construction disposition
`construction-01` was terminated by the enclosing execution tool's 45-second
limit. Nine complete case.json files and a tenth partial ready receipt remain;
no formal allocation had started. No experiment assertion failure was observed.
A direct startup probe measured about 1.447 s with ordinary site initialization
and 0.085 s with `-S`; these diagnostics are not research latency results.
Worker invocation was changed to `-S -B` before freeze, using standard library
only. `construction-02` then completed all 15 distinct cells and a separate
raw audit rejected 9/9 evidence mutations. All construction is excluded from
the formal result. The first timeout/partial evidence is retained separately.
