# Issue 3999: immutable byte-budget batches

Parents #3977/#3876; preserve closed #717 and every prior source/result. Owned branch research/passive-reader-byte-budget-20260922-v1. Additive namespace research/integration/passive_reader_byte_budget_batched_v2/. Prior namespace passive_reader_byte_budget_v1 remains unchanged.

## H
The exact experimental passive reader bounds the entire retained regular file, not its unread suffix. Consumed-prefix progress and max_records cannot clear an exceeded total-byte budget. Explicitly authorized finite expansion with the saved cursor returns only the unread record; resetting the cursor redelivers earlier records. This is a documented capacity boundary, not an upstream defect or a scalable recovery mechanism.

## T
Allocation byte-budget-batched-20260922-02, provided Linux x86_64/CPython3.13.5 execution container, no Docker/OrbStack image identity. No models/providers, external network in the experiment, GUI/input, installs, shared files or authority. Same ENVIRONMENT.json and exact unchanged run.py/upstream reader/CLI/DeliveryLedger from #3977 source commit298e9a196cae3d73800ba3a278aadb6325c90ac8.

The prior30s monolithic execution stopped after5 complete rows and one partial; it has no original terminal/manifest and its raw auditor fails. Never resume, pool or rewrite it. Only orchestration changes: six immutable consecutive two-case batches rather than one monolithic runner. Each batch calls the unchanged one() function; its three-second per-process/handshake limits remain unchanged. The frontend is still the experimental CLI under the upstream package alias, not the public runtime CLI or interactive_v17 producer.

Order: repetitions0,1; within each size1023,1024,1025; within each max_records1,32. Twelve fresh three-record streams,84 CLI calls. Per case: consume two initial records at1024/32; append complete third record to the chosen total; fixed1024/specified limit read; registered identical-bound comparison from original cursor; authorized2048/specified limit read; empty continuation; no-cursor reset at2048/32; changed-prefix refusal from original cursor at2048. Existing candidate and per-case oracle are unchanged.

Each launch creates an exclusive LAUNCH receipt. Each batch creates an exclusive CONSUMED marker, checks every preceding actual exit and prefix hash, checkpoints both fresh rows, and publishes its DONE receipt. A foreground parent waits25s maximum, retaining stdout/stderr and the actual exit or timeout. Tool envelope40s per batch. Stop at any incomplete batch; no retry, skip, replacement or threshold tuning. Only after all six actual zero exits may the parent create the aggregate manifest. Batch0..5 own ranges[0,2),[2,4),[4,6),[6,8),[8,10),[10,12). The sixth batch records aggregate completion without inventing a single common runner PID.

Commands, one invocation each from the source directory:
`python -B launch.py --out /mnt/data/issue3999/formal-02 --index INDEX --mode formal --freeze FREEZE.json`
INDEX is each integer0..5 in order. No invocation after a failed predecessor batch. Construction uses a separate2-case path and is excluded.

## D
PASS_WHOLE_STREAM_BUDGET_BOUNDARY_SCOPED requires12 rows/84 CLI receipts/12 writer exits and6 exact consumed/done/external-exit/range/prefix receipts. Below/equal1024 budgets return only record3; all4 oversized streams refuse both fixed-budget reads with STREAM_READ_BOUND_EXCEEDED/exit2/no next_cursor; all12 explicit expanded saved-cursor reads return record3 then empty/end; all12 reset comparisons return1..3, redelivering2 prior identities per case; all12 changed-prefix controls refuse CURSOR_PREFIX_CHANGED. Authority none/ACK false/input false throughout. Independent raw audit and13 rehashed corruption controls must pass. Complete contrary behavior FAIL; source/process/evidence/incomplete/timeout STOP/HOLD. No subset or predecessor pooling.

The auditor is independently implemented from the candidate but authored by the same assistant. Its per-case checks are byte-identical to the previous auditor; only aggregate orchestration checks change. It does not import run.py, batch.py, launch.py or upstream. Ten original corruption controls are unchanged, plus missing/nonzero batch exit and altered prefix hash. Hash integrity is not authentication or a proof of arbitrary auditor soundness.

## C / U
Batch pauses can change host timing, but timing is not a scientific endpoint. Exact byte counts have no rounding uncertainty; combined standard uncertainty and coverage factor are not applicable. Trusted single writer, stable regular files during each read, one lifetime and terminal process checks only. No crash durability, compaction, producer epochs, ACK/model consumption, bounded-memory performance, real task, production integration, token or latency claim. Larger budgets are finite headroom, not automatic recovery.

## Variables and unit check
| Symbol | Meaning | Unit | Definition | Domain | Type |
|---|---|---|---|---|---|
| L | retained stream length | byte (non-SI information unit) |len(stream bytes)|1023/1024/1025|integer scalar|
| B | caller byte budget |byte|max_bytes|1024/2048|integer scalar|
| O | consumed prefix offset |byte|cursor.offset|0 through L|integer scalar|
| R | record cap |1 (count)|max_records|1/32|integer scalar|

For valid arguments, L>B causes the B+1-byte read to exceed B before prefix verification or record extraction. Thus changing only O or R cannot avoid overflow. This follows from the actual source order, assuming the file is unchanged during the read. L, B and O share the byte unit; R is dimensionless. The experiment verifies real CLI/file/cursor binding, not a novel size-comparison theorem.

## Roadmap
Retain #3977 STOP -> excluded batch construction -> source/hash publication -> six first-outcome batches -> raw audit/13 controls -> lossless publication and evidence PR -> main readback -> only own dependency-safe branch cleanup. Broad #3876/#57 and repository ROADMAP remain open.
