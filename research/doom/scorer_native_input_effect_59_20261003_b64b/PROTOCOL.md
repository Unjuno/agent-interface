# Native POSIX scorer-input / exact file-sink composition

Worker `01a0ff52-b64b-71d2-b2d6-19a57b40283f`, FINAL-v5, parent #59.

H: exact #6913 engineering-v2 source services prequeued complete FINISH despite a returning eight-ms sample callback at a two-ms period, using real POSIX pipe/select/read, real perf_counter time and existing ScorerFileSink. T:16 fixed cells, original/repair × polling/stdin × zero/eight-ms authored sleep × full/one-byte read. Sources are copied unchanged from the identified commits; prior experiments are not imported. Alpha UTF8 and FINISH are prequeued before the loop; writer closes. A private completion JSON is the exact disposable effect. No game, model, GUI, physical input, live R134 allocation or shared runtime is used.

D: method PASS requires exact roster/types/source and artifact hashes, complete native I/O/callback/scorer/effect/cleanup joins, independently reconstructed scheduling receipts, private output, clock/cgroup/runtime records and named copied-raw negative controls. H_PASS_SCOPED requires all eight repair cells and four original zero-cost controls to complete exactly within64 completed samples, and four original overrun cells to reach the diagnostic sample cap without a command/effect. A finite cap is not infinite-starvation proof. Every first row remains; no retry, extension, tuning or removal. Unexpected child timeout/nonzero/output excess is infrastructure STOP with partial evidence; method/scientific failure is retained separately.

C: authored returning sleep, prequeued short input and finite diagnostic sample cap; actual sink/read fragmentation and OS scheduling may confound timing. Output pipe backpressure, nonreturning callback, floods, async producers and controller/game behavior are excluded. U: only this Linux/arm64 private Engine/Python image under observed host load; no distribution, rate, speedup, useful game feedback, physical release, natural workload/general liveness/privacy/security/safety claim. Reusing the sample clock's `useful` vocabulary does not create real task feedback; fixture ProgressSamples stay zero and nonterminal.

Six frozen source files, runner, separate data-only auditor, checks, deck, launcher and protocol are pinned before one formal candidate/one auditor. Ordinary disjoint construction is allowed before freeze; preserve first failures, separate minis and tests. Native wrappers delegate to perf_counter_ns/select/os.read and record calls; they are instrumentation, not fake services. One-byte wrapper intentionally limits native read request size. stdout/stderr≤64KiB per child, child3s, outer candidate30s/audit15s, total8MiB; sourceRO/networknone,1CPU/256MiB/pids64. Configuration and observed cgroups are distinct from adversarial enforcement. Common deadline remains unknown; no extension.

| Symbol | Japanese meaning | SI unit | Domain/assumption | Type |
|---|---|---|---|---|
| P | サンプル予定間隔 | ns | 2,000,000 | positive integer |
| c | 意図的に要求するsleep時間 | ns | 0 or8,000,000;実時間は記録から得る | nonnegative integer |
| B | 完了サンプルの診断上限 | 1 | 64;formal前固定 | positive integer |
| t | 実monotonic時計の観測 | ns | 同一child内で比較 | nonnegative integer |
| s | 予定サンプル時刻 | ns | 各receiptと別oracleで結合 | nonnegative integer |
| m | スキップした予定間隔数 | 1 | floor((decision_time-s)/P),非負 | nonnegative integer |

Scheduling identity: the initial scheduled time is the first native loop clock; each next schedule is previous schedule+(previous missed+1)P. The decision native clock immediately preceding the sample-start clock supplies floor((decision_time-s)/P). All clock timestamps originate from the real OS counter; no virtual-time cost is substituted.
