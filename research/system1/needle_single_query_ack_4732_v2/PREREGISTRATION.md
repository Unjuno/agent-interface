# Needle one-query acknowledgement — fresh successor #4813

Allocation `needle-single-query-ack-6911201-6911301-6911401-v2`; predecessor #4732 is preserved as formal `STOP_AUDITOR_IMPLEMENTATION_DEFECT` and post-hoc `HOLD_LATENCY_BUDGET`. No predecessor data are pooled or changed.

## H — hypothesis

For a resident synthetic online Needle adapter and durable snapshot, predicting the designated current query before acknowledgement, then the unchanged 512-row held-out vector after acknowledgement, reduces request→ack p95 versus predicting/returning all 512 rows before acknowledgement. Success requires query-only p95 <=60 ms and <=0.5× paired inline p95 on each fresh seed, with exact predictions, model/optimizer state, and durable bytes.

## T — treatment and frozen allocation

- Construction seed `6911101`; formal seeds `6911201`, `6911301`, `6911401`, no replacement.
- Reuse exact #4714 baseline `baseline/study.py` (Git blob `b055bd949a4489fc25e10b40ff7e6a44e233fb86`; SHA-256 `14d403f5f394fc4ac228609c5c137f09c153b777a45cedfe4abd895ff72ebf74`) for synthetic data/model/optimizer/checkpoint code. Rank-2 adapter, 16 support examples, 12 revealed arrivals, eight updates on current row, 512 held-out feature rows, no held-out labels in worker input.
- `INLINE_512`: update, score full held-out vector, durable atomic snapshot with file+directory fsync, reread/validate, return and acknowledge.
- `ONLINE_QUERY_ONLY`: matched update, score designated query, commit/reread same snapshot, return query and acknowledge; only after the supervisor has fully read and parsed ACK does it send `ACK_RECEIVED`. Worker waits for this receipt before running and returning the same full 512-row audit. This pre-freeze amendment removes the reviewed shared-one-CPU overlap between worker post-ack inference and timed supervisor receipt/parsing. Supervisor still waits for full audit before next arrival; no throughput/overlap claim.
- Same per-seed arm order frozen as INLINE first on 6911201 and 6911401, query-only first on 6911301. One Torch CPU thread per process; deterministic algorithms.
- One trainer orchestration and one independent auditor in pinned local Docker CPU image, network none, pull never, readonly source/root, 1 CPU/2 GiB/64 PIDs/no-new-privileges/bounded tmpfs. Preserve all raw outputs, inputs, snapshots, timing fields, exact commands and hashes.

## D — gates

Integrity requires all 72 formal arm-arrivals, no missed/duplicate arrivals, exact regenerated inputs/query schedule, no future/support-pool/held-out-label leak in worker input, exact independent query and full-vector parity, exact adapter and AdamW state, valid disk digest at every ACK, actual final-volume bytes matching final state, zero audit errors, and all five corruption controls rejected.

`PASS_QUERY_ONLY_ACK_LATENCY_SCOPED` only if integrity passes and every seed has query-only p95 <=60 ms and paired ratio <=0.5. Integrity mismatch is `FAIL_INTEGRITY`; integrity pass but latency miss is `HOLD_LATENCY_BUDGET`. Any source/image/Issue/readback/collision/pre-run provenance defect is STOP before formal. One formal orchestration, no retries/tuning/seed replacement.

## C — confounders

Tiny CPU synthetic data, local Docker storage, scheduler/fsync/JSON variability, fixed arm-order imbalance across only three seeds. Construction A (no ACK_RECEIVED handshake) gave ratio 1.199819; construction B with the review-driven handshake gave 0.928836. This shows the timing boundary matters; both are construction-only, no gate changes. Post-ack audit delays the next arrival and no queue-throughput claim is allowed.

## U — limits

No Cactus Needle 3 fine-tuning quality, live Astra corrections, GUI/task success, continuous per-frame learning, production durability, cross-host generalization or action authority. No product/runtime integration follows from a scoped timing pass.
