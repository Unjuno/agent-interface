# #4066 — sequential pages over a sealed snapshot

## Disposition
**STOP_WORKER_TIMEOUT; full scientific acceptance HOLD.** Preserve the first allocation. No formal rerun/replacement/pooling or postfreeze gate changes. #4066's scientific acceptance is not completed. This is an additive research evidence delivery, not runtime promotion; no broad roadmap closure.

24 of36 measurement workers completed (128/512 records; page1/32; three repetitions; two arms). The first2048/page1 baseline worker reached its frozen8s process limit and was killed/reaped with exit-9. Batch2 exited1 after8.43s; the20s supervisor did not time out. No2048 result was serialized. The other11 measurement workers and all12 formal controls were unstarted. It is unknown whether the killed worker had finished its timed drain before the separate accounting pass. Do not infer a2048 performance result or a formal-control result.

The frozen full auditor retains exit1 with24 reconstructed rows,0 controls, and exactly two missing-denominator errors. The separately labelled postformal prefix review has no row errors but sets full_scientific_acceptance=false. It does not replace the frozen audit or its HOLD.

## Scientific question / concrete integration decision
Can a bounded single-owner reader acquire a fully sealed static backlog once, keep its bytes and incremental prefix hash, and deliver the same sequential pages with less repeated work? #3985/#3988 changed only page limits; #3979 tested seal immutability. This study changes the reader's lifetime and algorithm at identical page sizes. It informs only a possible opt-in immutable-backlog session, not a stateless/live-file replacement or default setting.

Baseline uses the unchanged reader blob ea72c166c2cea511ea91031dfbb14563fe4e3245, on a real sealed memfd via /proc/self/fd. Candidate requires actual WRITE/SHRINK/GROW/SEAL flags before reading size, takes one bounded positional snapshot and incrementally hashes consumed LF-delimited records. It allows only values matching its current issued cursor. This equality check is not authentication. No checkpoint import, seek/replay, snapshot replacement, concurrency, crash retention or automatic recovery is implemented.

## Completed-prefix observations (descriptive; not full PASS)

Every paired sequential response is canonical-byte-identical and independently reconstructed from the original source records. Source-read/hash counters agree with the proof in PLAN. Authority=none and acknowledged/input_dispatched=false throughout the24 completed workers.

| Records | Page limit | Baseline CPU ms: median [min,max] | Candidate CPU ms: median [min,max] |
|---:|---:|---:|---:|
|128|1|94.639 [89.641,124.692]|4.919 [4.728,5.581]|
|128|32|6.344 [5.950,7.154]|2.263 [2.103,2.606]|
|512|1|1261.376 [1043.511,1312.007]|17.485 [15.151,20.832]|
|512|32|45.788 [37.769,50.748]|12.361 [10.628,16.252]|

At512/page32, cumulative logical source-read bytes are2228224 versus131072; SHA input bytes2359296 versus131072. This is17-fold and18-fold less logical work, not measured disk IO, a model-token reduction, or a production speedup. At that same cell, first-page wall medians are2.363ms versus2.053ms; candidate range2.003–2.872ms overlaps baseline2.115–2.716ms. No first-page benefit or distributional guarantee is inferred. The registered2048/page32 CPU<=0.50 ratio gate remains UNMEASURED.

Timer charged candidate initialization/copy, parsing, cursor creation and minimal in-memory bookkeeping. Imports, fixture/seal creation, warm-up, serialization and the declared accounting pass are outside it. Each arm uses a fresh process and the same256-byte records, page size and cap. AB/BA/AB order is not fully balanced. Candidate adds private memory linear in total snapshot length; RSS and disk traffic were not measured.

## H / T / D / C / U
H: under one immutable snapshot, sequential page equivalence plus one-pass read/hash work; separate CPU-benefit hypothesis at2048/page32.
T: prospective36-worker/12-control allocation in three size batches; source hashes publicly committed/read back before any formal run. Actual24 workers plus one timed-out attempt retained. Two excluded construction blocks remain separate.
D: full gates NOT MET due incomplete denominator. Complete-prefix equivalence/count observations are retained without promoting full PASS. The timeout is an execution limitation, not a scientific contradiction or a reason to restart until favourable.
C: trusted owner/snapshot, same byte lifetime, private reader state, kernel sealing and coherent acquisition are assumptions. More memory/state and loss of stateless cursor import are real contract costs. Correct response is not host retention, consumption, ACK, latest state or input authority.
U: real producer/host composition, live append, restart, concurrent consumers, provenance authentication, GUI/model benefit, tokens, general performance and production remain unmeasured. Three repetitions give descriptive medians/ranges only, not reliable tails or calibrated uncertainty.

## Chronology, engineering records and audits
Intake main2308b8301d69b7089a2e0636486736ed59b61537; preformal main33e86e997d02b769af17a3f03f6035c68927da6e. Source commitment16a5e97baee5c2ca1d597562ed2441d29d796987; FREEZE SHA256c6b8c54cd5808d26a181ec0ab7a8c7629352ba97305d4bf1b4440b496dfd4a9f. Git blob af3baec858bf0601495304efb4b383e9f658f9ed matched local bytes before execution. Fourteen source/environment/plan hashes stayed unchanged.

Construction01 completed4 workload workers and12 controls but exposed high site-startup cost; original sources/output retained. Construction02 changed both arms to -S before freeze;4 workload workers/12 controls completed, eight units and8/8 rehashed semantic corruption controls passed. Neither construction contributes formal rows. The formal8-second worker budget still failed at the largest baseline; this planning limitation is not hidden.

Frozen full AUDIT.json: exit1,24 worker rows/0 controls, two missing files. Postformal PREFIX_REVIEW.json: exit0, completed-prefix reconstruction only. A supplementary8-mutation prefix challenge invocation hit its outer30s tool timeout before writing a result/exit summary; original empty stdout/stderr and PREFIX_CORRUPTION_STOP.json are retained. No formal corruption PASS is claimed; the earlier8/8 is CONSTRUCTION ONLY. No further benchmark or mutation-run retries were used to obtain a green status. Postformal scripts are labelled, separate from frozen code. Same-author separately structured auditor/process is not independent human review.

All25 attempted workers have actual exit receipts:24 zero, one-9. Successful batch supervisors0/1 exit0; failed batch2 exit1. Subsequent process inspection found no remaining owned worker. No model, GUI, native input or external experiment network was involved.

## Environment
Provided Linux6.18.44 x86_64 container, CPython3.13.5, OpenSSL/hash and executable identities in ENVIRONMENT.json; guest Intel Xeon E5-2673 v4, affinity0..4, cgroup CPU quota400000/100000. Nominal CPU model text is not a measured clock; frequency/load/physical-core isolation were uncontrolled. Docker/Podman/gh CLI absent, no Docker/OrbStack/image-attestation equivalence. All clocks are same-process ns; CPU and wall are separate. No combined timing uncertainty or coverage factor is invented.

## Review without rerunning the experiment
From the publication directory, `python -S -B unpack.py /tmp/issue4066-review` to a fresh destination. In that destination:

```
python -S -B -m unittest -v test_candidate
python -S -B audit.py formal --out REVIEW_FULL.json
# EXPECT exit1: original full-denominator HOLD must remain.
python -S -B prefix_review.py formal --out REVIEW_PREFIX.json
# EXPECT exit0 with full_scientific_acceptance=false.
```

Do NOT invoke consumed batch.py allocations. Full proof, variable/unit table, exact sources, original construction versions, raw responses, timed/counter receipts, all failures and source commitments are in the data-only capsule. Packaging hashes establish integrity, not external authenticity. Repository-wide CI/review is a separate delivery gate.

## References
Python3.13 os.pread/memfd_create and fcntl documentation; Linux man-pages F_GET_SEALS/F_ADD_SEALS. Incremental hashing and byte-count proof are fully expanded in PLAN. Primary API semantics motivate the design; the local measurements alone determine this finite result. No novel OS theorem is claimed.
