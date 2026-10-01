# Cooperative warning latch: producer restart experiment

Decision: **PASS_PROCESS_RESTART_SCOPED**. Retain transactional persistence of the unchanged EventLatch rules as a cooperative single-slot candidate, not a production change.

Issue #214; immutable BASE `4e8e197115969df81a946176e08362c130136603`. No shared runtime, workflow, existing scorer, historical allocation, GUI, game or model execution is changed.

## One-factor question

The uploaded `quiet_window_ack_latch_v1/latch.py` retains warnings in memory only. Both arms execute its exact source (SHA-256 `bcf64205122d1d593949f9fbfcaaaa06b59f8920e4cb130c3c705a552a3ac2ba`). Only storage changes. The candidate atomically persists producer scope, next sequence, pending sequence, last acknowledged sequence, and historical condition state. ACK is not condition resolution and never grants input authority.

## Retained first failure and separately frozen successor

Allocation 005 was frozen in #214 comment 5686064419. The outer 45-second tool invocation terminated it after 23 complete cases (10 durable, 13 volatile) and one incomplete directory, `023-end_after_commit-durable`. All 23 complete records match their arm-specific expected observations. The incomplete case is UNKNOWN. Original source, preregistration, raw records and databases are preserved. No same-ID resume or pooling occurred.

Allocation 006 was frozen separately in comment 5686098917, prereg SHA-256 `339d2ec36b934e83b64a32f4d296ec08920e11e89b3e71c8618615b058e3d00b`. Only execution orchestration changed: a tracked private subprocess was actively polled within the response. Measured source bytes and the finite schedule stayed unchanged. All 80 first cases completed; no experiment process remains running.

## Environment and design

CPython 3.13.5; SQLite 3.46.1; Linux 6.18.44 x86_64; AMD EPYC 9V74 shared host, affinity 0..4, unpinned CPU frequency; overlayfs. Candidate: SQLite DELETE rollback journal, synchronous FULL, BEGIN IMMEDIATE, trusted local directory, one fresh database per case, one-second connection busy timeout. Missing stores, wrong producer scope and corrupt storage refuse rather than silently initializing a new empty producer.

Five repetitions x eight scenarios x two storage modes = 80 serial cases. The explicit schedule is shuffled once with seed 21420260916. The parent waits for a child checkpoint, sends real SIGKILL and verifies returncode -9. New child processes inspect recovery and perform bounded replay. The two construction cases are retained separately and excluded.

Scenarios: pending restart; begin before commit; begin after commit/pre-reply; ACK before commit; ACK after commit/pre-reply; condition end before commit; condition end after commit; delayed old ACK after restart with a newer pending event.

## Results

| Endpoint | Volatile | Transactional |
|---|---:|---:|
| Desired recovered-state contract satisfied | 5/40 | **40/40** |
| Old ACK incorrectly clears a newly created event | **5/5** | **0/5** |
| Arm-specific expected observations accounted for | 40/40 | 40/40 |

The five volatile contract passes are empty-state rollback controls, not evidence of event retention. Other volatile cases lose pending state or sequence/ACK history.

A concrete identity bug appears after restart: memory resets the next sequence to 1, so a delayed ACK for an old sequence 1 can clear a new event also numbered 1. Persistence retains the high-water mark and pending sequence 2; the old ACK returns DUPLICATE without clearing it.

Before-commit kills restore preceding committed state. After-commit/pre-reply kills restore new state despite the missing reply. Begin retries return BUSY while the slot remains pending; committed ACK retries return DUPLICATE. This is not external exactly-once execution. Events before creation commits and external application effects are not atomically coupled to the local store.

The recovered condition bit is historical, not proof of current application truth. Revalidate application conditions before any new action. No recovered field renews input authority.

## Descriptive cost

Seven alternating-order batches per arm; 100 begin/end_condition/ACK cycles = 300 operations per batch. These are medians and ranges of **batch means**, not individual-operation tail percentiles. Process launch, DB initialization and connection opening are outside the timed loop; wrapper serialization and state reads remain included in both arms.

| Storage | Median batch mean / operation | Observed range |
|---|---:|---:|
| Volatile wrapper | 0.005283 ms | 0.004903-0.011400 ms |
| Persistence wrapper | 0.082835 ms | 0.078167-0.105423 ms |

Persistence is slower and is retained for correctness, not speed. Overlayfs measurements do not establish physical-device fsync latency. Do not place this work on the input-owner thread based on this study.

## ERROR CHECK

The read-only auditor imports neither EventLatch nor LatchStore. It compares manually declared expected states, checks all 80 schedule identities and SIGKILL checkpoints, verifies absence of fabricated lost replies, replay results, database integrity and 142 retained file hashes. Eight audit corruptions are rejected: erased pending state, reset sequence, changed scope, fabricated clean exit, old ACK acceptance, authority regrant, failed integrity and invented reply.

Additional controls reject missing/wrong-scope/corrupt stores, malformed/foreign ACKs, and duplicate ACK against the next event. ACK while a condition remains active preserves the visible warning. Full archive reconstruction restores 200 exact files and reproduces the independent audit. This is independent checking code in the same session, not independent human/agent review.

Units: integer elapsed nanoseconds divided by 1,000,000 yield milliseconds; dividing by 300 gives the per-operation batch mean. Reported clock resolution 1 ns is not timing accuracy. No calibrated combined uncertainty or coverage factor is claimed.

## H / T / D / C / U

H: atomic persistence of unchanged state prevents committed pending-event loss and old-ACK identity reuse across process restart.
T: fixed 80-case SIGKILL/restart block, eight corruption controls and seven cost batches per arm; stopped allocation 005 remains separate.
D: 40/40 candidate state contracts pass. Retain the mechanism at the stated scope only.
C: stable scope and surviving trusted storage are added assumptions; request delivery ambiguity, events before commit, multiple pending events and external effects remain unresolved.
U: one host, process kills at chosen boundaries, no kill inside COMMIT, no power-loss/kernel-crash test, no live GUI restart, model, gameplay, or production promotion. FULL in rollback mode is not asserted to guarantee durability across every power failure.

Next single question: connect this unchanged persisted state to the existing cooperative rendered fixture and restart its producer with a pending warning. Require stable identity, restored visual notification and no automatic input regrant; do not change polling cadence simultaneously.

Implementation references: https://www.sqlite.org/lang_transaction.html ; https://www.sqlite.org/atomiccommit.html ; https://www.sqlite.org/pragma.html#pragma_synchronous . Documentation explains the chosen mechanisms, not coverage of untested failure models.

## Reconstruction (offline; no new benchmark)

From this directory:

```sh
python reconstruct.py /tmp/quiet-latch-restart-retained
python /tmp/quiet-latch-restart-retained/new-study-006/audit.py /tmp/quiet-latch-restart-retained/measured-restart-02 /tmp/quiet-latch-restart-retained/new-study-006
```

`manifest.json` binds each binary part by byte count, SHA-256 and Git blob identity. Parts are complete pieces of a lossless JSON/XZ archive, not placeholders. Exact sources, preregs, all 80 raw case records, stopped-005 evidence, databases, controls and cost records are retained. Reconstruction never imports or executes archived study code.

`prior_audits.json.xz` separately contains four exact prior-audit/source files. It does NOT contain the previous 120/40-case raw GUI archives. See `research/retention/quiet_watch_pending_20260916/README.md` for that explicit remaining retention boundary.
