# Single-acquisition historical image presentation — c7r8

Issue #4404; allocation `review-snapshot-c7r8-20260926-01`.
Source base: `4c701cc51b06296268ad8d9ae3eff1dd6f2d379d`.

## Objective and one changed factor

Measure the cost of returning the PNG byte snapshot already read by the selector,
instead of reading and hashing the file a second time in `review_bytes`.
This is not PNG qualification, compaction, native capture, or model timing.
The unchanged five upstream modules are restored byte-exactly from the supplied
#4080 archive and matched to current GitHub blob identities. No old experiment
is rerun. The baseline uses complete functions, without CLI API initialization;
the candidate changes only two copied modules. CANDIDATE.diff shows every delta.

## H / T / D / C / U

H: under an explicitly immutable-file contract, one acquisition returns the exact
same complete presentation while eliminating one logical PNG read and hash. A
processing benefit is possible, not assumed.

T: six immutable synthetic RGB PNG workloads, three geometries crossed with zlib
levels 0 and 6; exact recipe and order in PLAN.json. One fresh worker per workload,
two excluded warmup pairs, 21 measured pairs, alternating policy order. Both
policies consume the same report bytes and same file path. Canonical output JSON
serialization is timed. Input generation, imports, output hashing and verification
are outside timing. Separately instrument Path.read_bytes only after timing, once
per policy, to account for logical read calls/bytes. Four untimed refusal/diagnostic
controls use a different small geometry. Small construction is excluded.

D: require all six first worker exits, 252 measured outputs, 24 warmup outputs,
12 accounting outputs and eight control outputs; exact canonical response parity,
full image payload and original receipt/summary parity, two-versus-one positive
read counts, no input mutations, source integrity and independent raw audit.
At least eight effective, well-formed modified-evidence controls must reject.
Successful characterization is PASS_SINGLE_ACQUISITION_PRESENTATION_SCOPED, not a
performance/adoption PASS. Fidelity contradiction is FAIL. Incomplete evidence is
STOP/HOLD; do not regenerate failed/missing rows. No optional stopping, deletion,
replacement, threshold tuning or pooling with construction/earlier allocations.

C: trusted quiescent artifacts for the duration of one call, stable exact report
bytes, no concurrent writer, same paths, no capture restart, no input or model.
Warm page cache, one logical CPU affinity (not exclusive hardware); frequency and
host interference unregulated. A second read is an explicit change-detection
point in the original code. This proposal removes that point and is NOT equivalent
for concurrently mutable files. No original result is retroactively invalidated.

U: processing-time distributions are technical repeats of six synthetic conditions,
not a population estimate, calibrated physical clock uncertainty, or GUI/model
latency. Cold storage, all modes/schemas, whole-process memory, source authenticity,
decode validity, live delivery and production integration remain untested.
The old qualifier's same-dimension wrong-image limit remains applicable.

## Execution and process evidence

`python -B -S execute.py formal INDEX`, INDEX 0..5, one synchronous call each.
Each invokes worker.py once with a 20-second child limit. The exclusive started
marker prevents an unnoticed rerun; an incomplete preceding condition stops the
next. After six successful conditions run `python -B -S execute.py controls` once.
All stdout/stderr, actual child PIDs/exits, primitive clocks, first complete output
bytes, subsequent output identities and original PNG/report/RGB inputs are kept.
New directories only. No persistent service remains after the request.
Public readable source/plan/environment/freeze and ownership recheck precede formal.

## Variables and units

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain/assumptions | Type |
|---|---|---|---|---|---|
| B | 符号化PNGの長さ | 1 (byte count; byte is non-SI information unit) | len of retained PNG bytes | positive integer | scalar integer |
| W,H | 画像幅・高さ | 1 (pixels) | IHDR dimensions | fixed PLAN.json positive integers | scalar integers |
| x,y | 画素位置 | 1 (pixels) | column and row | 0<=x<W, 0<=y<H | scalar integers |
| t0,t1 | 呼出し開始・終了の単調時刻 | s | perf_counter_ns samples multiplied by 10^-9 | same process/clock | scalar real |
| c0,c1 | 開始・終了の累積プロセスCPU時間 | s | process_time_ns samples multiplied by 10^-9 | same process/clock | scalar real |
| T | 関数とJSON直列化の経過時間 | s | t1-t0 | nonnegative | scalar real |
| C | 同じ区間のCPU時間 | s | c1-c0 | nonnegative | scalar real |
| r | 対応する候補/基準経過時間比 | 1 | T_candidate/T_baseline | baseline duration positive | scalar real |
| Rb,Rc | 基準・候補の論理読取りバイト数 | 1 (bytes) | sum of successful counted read lengths | stable positive image path only | scalar integers |

Dimensional check: T and C subtract timestamps with the same clock and seconds;
r divides seconds by seconds and is dimensionless. No X11 time, wall-clock epoch
or remote timestamp is subtracted. Logical bytes are not measured physical disk IO.
Reported nanoseconds are software clock resolution, not calibrated accuracy.
No combined standard uncertainty or coverage factor is asserted.

## Conditional equality argument

1. Hold request bytes, metadata, path resolution and file contents fixed during a
call. Let the single image contain exactly the B retained bytes.
2. Both selectors execute identical reference/sequence/path checks and read those
same bytes. Their SHA256 strings and returned metadata are identical.
3. The baseline discards that first buffer, reads the immutable file again and
compares its hash. Equality follows because the bytes did not change. The candidate
passes the first immutable Python bytes object to the presentation function instead.
4. Every remaining metadata/digest/PNG-signature/base64/result step is identical.
Both therefore encode the same image and preserve the same source and outcome
fields; canonical JSON is byte-identical. Missing/hash-invalid/no-observation
controls retain the relevant shared rejection/no-image paths.
5. At this positive boundary Rb=2B and Rc=B. These are logical reads; the cache may
satisfy both without a physical disk read. Removing one read/hash does not prove a
wall-time speedup, because allocation, cache and scheduling differ.
6. If file contents change between the baseline's acquisitions, premise 1 fails:
original code may refuse while candidate returns an earlier historical snapshot.
Neither this argument nor this experiment qualifies that behavior as a drop-in
mutable-file replacement, currentness, authentication, or action authority.

ERROR CHECK: equality is conditional, not global. Hash equality alone is not used
to prove origin. Exact full byte parity is the measured gate. Source-preservation
and delivery are separate from production adoption. Source memory lifetime can
change; no memory benefit is claimed without a memory measurement.

## Priorities and handoff

This supplies evidence for #3544/#2789's caller-side observation/result cost choice.
#4395 owns compaction cost with no images; #4350 owns historical diagnostic mapping.
No shared runtime or foreign branch is changed. The previous #4080 study is closed
and remains canonical. After a retained result: complete additive evidence PR,
exact-head checks/scoped review, qualified evidence merge/readback, then only
supported dependency-safe cleanup of this branch. Global ROADMAP remains open.
