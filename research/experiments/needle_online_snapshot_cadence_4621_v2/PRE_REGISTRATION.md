# Needle online-LoRA snapshot-cadence experiment — Issue #4621

Allocation `needle-online-snapshot-cadence-4621-v2`. This is a fresh-seed successor to the v1 STOP on #4615, not a retry. V1 stopped before training because of a host freeze-preflight schema mismatch. Preserve that STOP and all source bytes unchanged.

## H — hypothesis

Rank-2 candidate skills can continue updating after each of 16 synthetic teacher-feedback arrivals while persisting/resuming every 4 or 16 arrivals, with exact equality to uninterrupted state and held-out predictions. Less frequent durable snapshots may reduce the amortized persistence/restart cost. The immutable active base is never modified and candidate updates have no execution authority.

## T — frozen experiment

- Fresh seeds: 77111, 77222, 77333. All data, schedule, and initialization offsets are deterministic and recorded. No replacements.
- Same bounded synthetic family as #3911/#4507: 8-dimensional inputs; hidden width 16, tanh; 4-way action labels; role A uses the base policy, role B requires flipping the first binary factor; rank-2 output LoRA; 512 base rows and 400 AdamW steps; 16 sequential feedback arrivals; 8 adapter AdamW steps per arrival with batch size 32; LR 0.025 for base training and 0.04 for LoRA; 4096 held-out examples per role.
- Paired arms share identical generated examples, labels, update order, minibatches, initialization, optimizer, and evaluation set: uninterrupted reference; restart/checkpoint cadence K=1, K=4, K=16. Updates always occur at each arrival; K affects only the persistence and fresh-process restart boundary.
- Checkpoints contain adapter weights, full AdamW step/moments, immutable-base digest, seed, role, cursor, schedule version/digest, and canonical payload digest. Every resumed worker validates before optimizer access.
- Retain per-arrival held-out predictions and adapter/optimizer state, every checkpoint byte/hash, update times, checkpoint write and fresh-process start/load durations, process count, raw data, output, commands, environment and source hashes. Independent auditor is separately implemented and recomputes held-out predictions/metrics from raw examples and recorded states without importing runner code.
- One formal orchestration, zero retries/tuning/seed replacements. Local `needle-pilot05:local`, exact image ID in freeze, Linux/amd64 CPU only, one thread, network disabled, read-only source/root, 1 CPU, 2 GiB, 64 PIDs. No image pulls, package installs, GPU, GUI, input, provider/network access, or user data.

## D — decision rules

Integrity PASS requires all frozen source/input/checkpoint hashes to validate, the independent raw-only auditor to report zero errors, and all route/snapshot controls to pass.

For every seed, cadence and feedback cursor, adapter tensors, optimizer state and held-out predictions must exactly match the uninterrupted reference at every resumption boundary and at completion. Base tensors must remain unchanged. This is a necessary resumability gate; underlying B accuracy is reported but is not used to claim task utility.

Report (a) update-only p95 across all feedback arrivals, (b) checkpoint-write plus fresh-process-start/load overhead per checkpoint, (c) that persistence overhead amortized per feedback, and (d) total per-feedback latency including its amortized persistence cost. A cadence is a scoped persistence candidate only if exact-state/evidence gates pass, update-only p95 and total amortized per-feedback p95 are each <=60 ms, and its amortized persistence overhead is at least 20% below cadence K=1. Report the maximum possible unsaved feedback on a crash as K-1; do not hide the durability tradeoff.

Invalid schema/version/role/base/schedule identity, corrupt digest, stale cursor, duplicate cursor, and skipped cursor must be rejected before state advance. Any missing evidence, mismatch, infrastructure failure or audit flaw is a typed STOP/HOLD, not a quality result. No postformal correction, rerun or tuning.

## C — alternatives / failure modes

Fresh process startup or JSON validation may dominate snapshot cost; K may not materially reduce persistence overhead. A reduced snapshot frequency trades recovery-point loss for throughput. Serialization may alter floating-point or AdamW state. Exact synthetic resume does not imply useful learned behavior.

## U — limits

Three deterministic seeds, one authored synthetic task family, one tiny model and one local CPU container. No real Astra feedback, GUI/app effect, concurrent training/inference, cross-hardware timing claim, live action authority, general skill transfer, or production claim. This is discrete feedback-conditioned candidate learning, not continuous per-frame weight updates.

