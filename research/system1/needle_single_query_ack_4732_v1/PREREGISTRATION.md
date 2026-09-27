# Needle one-query acknowledgement vs inline held-out batch scoring

Issue #4732; successor to #4714. Allocation: `needle-single-query-ack-6842791-6842793-6842797-v1`.

## H — hypothesis

In a resident one-row Needle feedback worker with a durable snapshot, scoring and returning all 512 held-out predictions before acknowledgement is a benchmark-only cost. Predicting the designated current query before durable ack and calculating the same full 512-row held-out vector after ack will reduce measured request→ack p95 to <=60 ms and <=0.5× the matched inline-512 path on each fresh seed, with identical query predictions, full held-out vectors, adapter/AdamW state, and checkpoint bytes. The treatment moves a fixed evaluator calculation out of the synchronous response; it is not an assertion of lower total compute or stable queued throughput.

## T — frozen treatment

- Formal seeds `6842791`, `6842793`, `6842797`; no replacements. Construction seed `6842783`, disjoint from the formal block and #4714's construction/formal seeds.
- Use the exact immutable #4714 `src/study.py` as the data/model/optimizer/snapshot implementation at SHA-256 `14d403f5f394fc4ac228609c5c137f09c153b777a45cedfe4abd895ff72ebf74`; mount read-only at `/baseline`. New runner and auditor live at this Issue's additive evidence path and never edit the predecessor.
- Same synthetic model/data family and offsets, 400 base AdamW steps, rank-2 LoRA, 16-row support set, 12 revealed feedback arrivals, exactly 8 adapter updates on the current row, and same 512 unlabeled held-out feature queries. One query id per arrival is fixed as `(arrival_index * 37 + seed) % 512`; it carries no target label.
- `INLINE_512`: update; infer all 512 held-out queries; write file+directory-fsynced atomic snapshot; reread/validate; return whole prediction vector and ack.
- `ONLINE_QUERY_ONLY`: matched update; infer only the designated query; write/reread the identical durable snapshot; return that query prediction and ack; only after that response is flushed, infer all 512 held-out queries from that exact committed model state and return a separate `POST_ACK_AUDIT` record. The supervisor waits for that record before sending the next feedback. Thus there is no inference/feedback overlap and no throughput or queueing claim.
- Both arms use the same new Docker local volume, worker startup/input, container, schedule, and rows; arm order alternates by seed. Worker input excludes support pool, schedule, held-out labels, and all future feedback. The only treatment is scoring/returning the full batch before ack versus single-query response plus post-ack audit batch. This includes compute and response serialization/parsing, and is measured as one response-path placement factor.
- Construction uses only seed `6842783`, 12 arrivals, then a separately invoked auditor; never interpret this as formal evidence. Formal uses one trainer orchestration and one independent auditor. Container: cached `needle-pilot05:local`, exact image id to be recomputed and frozen; Linux/amd64 CPU, network none, pull never, read-only root/source, 1 CPU, 2 GiB, 64 PIDs, no-new-privileges, bounded tmpfs. Fresh dedicated Docker local volume and fresh empty training/audit directories. No retry, tuning, seed replacement, or post-result extension.
- Retain all runner inputs, per-arrival requests, acknowledgements, full post-ack vectors, states, stage timings, logs, actual final volume bytes, independent audit and checksums. Auditor does not import runner code; it independently replays updates and predictions from the frozen common model/data source and retained raw input.

## D — decisions

Integrity PASS requires 72 arm-arrivals, zero missed/duplicate arrivals, exact requests/query IDs, exact single-query and 512-vector parity with an independent replay, exact adapter and full AdamW state at every arrival, valid per-ack canonical durable digests, actual final bytes equal the final acked state for both arms, held-out/future labels absent from worker input, zero audit errors, and five corruption controls rejected.

`PASS_QUERY_ACK_PATH_SCOPED` only if integrity passes and for each formal seed `ONLINE_QUERY_ONLY` acknowledgement p95 <=60 ms and <=0.5× paired `INLINE_512` p95. Any integrity failure is typed `FAIL_INTEGRITY`; if integrity passes but either latency gate misses, disposition is `HOLD_LATENCY_BUDGET`. A pre-training source/image/volume/auditor/environment failure is typed STOP. One frozen orchestration only.

## C — competing explanations

The single query, adapter update, fsync/readback, JSON response, or host scheduling may still exceed 60 ms. The full batch may dominate only because 512 rows are an artificial per-feedback workload. Post-ack scoring may delay the next feedback; this design waits for it and measures total elapsed time separately, so it cannot claim queue throughput or asynchronous overlap benefit. The local Docker/WSL2 storage driver remains host-specific.

## U — scope

Three synthetic seeds on one Windows/Docker Desktop + WSL2 host, one tiny model, and one local volume. Not Cactus Needle 3 LoRA quality, Astra corrections, GUI/task success, continuous per-frame online fine-tuning, production durability, multi-host behavior, or action authority. #4205's actual Cactus Needle 3 candidate remains a failed prerequisite for #4680.
