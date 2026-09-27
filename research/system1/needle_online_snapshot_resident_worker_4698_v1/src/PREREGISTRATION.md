# Resident single-owner worker for online Needle snapshots

Issue #4698; allocation `needle-resident-checkpoint-6842711-6842713-6842717-v1`.

## H

The #4621 snapshot-cadence study achieved exact resume but no cadence met its 60 ms total-feedback p95 gate; K=1 was 2.454 s p95 and worker startup/state restoration dominated. Hypothesis: one resident single-owner process that fsyncs an atomic complete snapshot after every feedback can preserve exact adapter+AdamW continuation while reducing feedback-to-durable-commit p95 to <=60 ms and <=half the matched fresh-process control, with no acknowledged dirty feedback.

## T

Fresh seeds 6842711, 6842713, 6842717. Base/support/held-out/base-init/base-batch/order/adapter-init use offsets +1/+2/+3/+10/+11/+21/+20. No replacement. The +22 batch-stream offset from the initial draft is unused: the clarified treatment repeats only the arrival row. Reuse the bounded #4621 CPU model family: 8→16→4 base, rank-2 output LoRA, 400 base AdamW steps, a fixed 16-row support pool with the first 12 rows in seeded order as sequential arrivals, and exactly 8 adapter AdamW updates on the newly arrived row per arrival. Only that row and its derived label are sent in the request. The worker input file excludes all support rows and schedule. Held-out input has 512 fixed feature rows, no labels; predictions are compared only for exact parity, not adaptation-quality claims.

- `RESPAWN_K1`: one new isolated Python worker per feedback; each loads the prior committed adapter+optimizer state, applies 8 updates to only the newly revealed row, writes a complete snapshot to a new temp file, fsyncs, atomically replaces the checkpoint, fsyncs the parent directory, then replies.
- `RESIDENT_K1`: one long-lived single-owner worker handles all 12 identical arrivals and performs the same commit protocol at each feedback boundary. It reloads and validates the committed snapshot before acknowledging each request.

An uninterrupted deterministic reference provides exact adapter, AdamW and held-out-prediction states after every arrival. Record host-observed request→ack latency, startup, update and file commit separately, full run time, and break-even arrival. The trainer retains matched per-arrival request, response, snapshot, prediction and per-arrival digest evidence. The independent auditor implements the forward/training oracle separately and checks every one of 72 arm snapshots, every request binding, predictions, exact seed/base/cursor/optimizer-step bindings, durable-byte hashes, worker-input information boundary and raw input/base hashes. Base weights must remain immutable.

One local Docker orchestration using cached tag `needle-pilot05:local` and the image ID pinned by #4621; Linux/amd64 CPU, PyTorch 2.5.1+cpu, no network, read-only root/source, one CPU, 2 GiB, 64 PIDs. Trainer and independent auditor use separate containers. No pulls, installs, retries, tuning, seed replacements, GUI/user data, external effects, or model/action authority.

## D

`PASS_RESIDENT_SNAPSHOT_LATENCY_SCOPED` only if all 3×12 snapshots for both arms exactly match the independent uninterrupted adapter/AdamW/prediction reference; all durable hashes and current cursors verify; base is unchanged; independent audit errors are zero; resident p95 is <=60 ms and <=0.5× respawn p95 for every seed; and resident startup + first 8 committed feedbacks breaks even with the paired respawn total by feedback 8. Every acknowledged update must have a verified complete snapshot. `FAIL_RESUME_DIVERGENCE`, `FAIL_DURABILITY_OR_LOSS_BOUND`, or `HOLD_LATENCY_BUDGET` apply as described in Issue #4698. A source/image/auditor fault is typed STOP, never scientific failure. One orchestration, no reruns or post-result extension.

Construction-only `--smoke-one` is a distinct non-formal mode: first seed, first arrival only; full-path construction uses `--formal` in a separate empty construction directory and is audited with `--construction-full`, which cannot return formal PASS. These modes verify process protocol, request information boundary and oracle wiring only; their measurements and disposition never enter formal gates. The no-label/one-new-row clarification was appended to Issue #4698 before freeze after code review found the initial draft was ambiguous about future labels/support access. The original Issue text remains visible for provenance.

## C

The earlier persistence p95 may be host scheduling or serialization rather than process creation. A resident worker may introduce hidden mutable state, stale cursor or shutdown hazards; its single-owner invariant and durable acknowledgement are explicit. Tiny synthetic training and a single Docker Desktop host constrain external validity.

## U

This tests worker lifecycle and checkpoint continuation only. It does not establish adaptation quality, useful skill transfer, Astra supervision, GUI behavior, production latency, multi-host durability or authority safety.
