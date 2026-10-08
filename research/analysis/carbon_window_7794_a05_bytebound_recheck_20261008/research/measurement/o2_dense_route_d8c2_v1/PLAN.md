# All-dirty O2 routing — prospective CPU experiment d8c2, Issue #4340

## Scope, provenance and roadmap

Intake main46e85863a9d0bfa9f5b7648fd81f3423907ca106; reservation base9bc9343564a1522df2cf62f4c5cfcdb38194b7c4. MCP inspected README, CURRENT_GOAL active section, ROADMAP, recent open/closed Issues/PRs, first100 branch names and targeted dense/skip searches. #4065's raw-cost discussion supports further scan/assembly investigation but its overall HOLD remains unchanged. #4092/#4103/#4139 already improved contiguous tile materialization; the exact current canonical implementation is the control here. No old allocation is rerun. Searches are bounded/non-atomic; unpushed work is unknown.

Own research/o2-dense-route-20260925-d8c2 and research/measurement/o2_dense_route_d8c2_v1 only. No shared runtime/workflow/index modification. No code or capsule from blocked #4331/#4333/#4322/#4337 is used or republished. This is a different image-encoding-cost question, not a means of republishing blocked source.

Exact vendored source identities: observation_tiles/tile_transport.py Git blob0de27f79e6cbf5ded545430b26a87dcacc142b71; observation_gating/exact_gate.py blobd2629bc94d40cc0a8e1bf9e053585549218629ed. Both originate from the canonical repo, Apache-2.0, and are kept byte-exact. Ordinary imports, no stubs or AST omissions. GitHub source acquisition used MCP. Direct raw-URL acquisition failed at DNS; an initial manual exact_gate transcription differed in one Receiver assignment and was corrected BEFORE import/tests; the rejected copy is retained in construction. Both exact Git objects now match.

Roadmap: intake/source parity -> excluded construction -> public complete source/hash freeze and readback -> three one-shot timing batches -> stdlib raw audit and ten effective controls -> complete evidence PR -> exact-head checks/scoped review -> evidence-only merge/readback if qualified. No adoption of the candidate into canonical O2 and no completion of the global roadmap.

## H

Detect all dirty tiles first. If every tile differs, keep the already prepared full packet without constructing/compressing the tile alternative; otherwise preserve canonical tile order and smaller-packet selection. This may reduce dense update encoding time at acceptable wire cost. Every tile dirty does NOT mathematically imply full-frame compression is smaller.

## T

Provided Linux container, CPython, installed NumPy and zlib; actual identities in ENVIRONMENT.json. One selected allowed logical CPU via sched_setaffinity, batch1 frame, warm memory, no fixed frequency/CPU exclusivity. Docker/gh unavailable; no Docker/OrbStack image attestation. No GUI/model/provider, task input, network experiment, package installation or user data.

Fully specified NEW synthetic RGB pairs from fixtures.py: geometries129x97,320x240,641x481; UNCHANGED,LOCAL,SCATTER,DENSE_SOLID,DENSE_PATTERN,DENSE_TILE_REPEAT. INPUTS.json hashes all36 exact before/after byte arrays before measurement. Six scenes per size =18 conditions. Tile edge64; actual canonical zlib compression level1 and identical metadata.

Unchanged canonical Encoder versus opt-in DenseEncoder. Each paired iteration initializes a fresh encoder and encodes the base OUTSIDE timing. Timed portion is one update encode only. Hashing, independent checks, storage and construction of inputs are outside timing. Two warmup pairs then15 measured pairs per condition, alternating order by batch/scene/iteration.270 measured pairs/540 measured update calls and36 excluded warmup pairs/72 update calls. The base calls are additional untimed work, not concealed end-to-end work. Not a live acquisition or model-task latency test.

Three separate six-condition batch processes, commands python -B execute.py 0, then1, then2, once each. Child timeout35s; caller envelope45s. Existing output/receipt refuses launch. Each first partial is retained; stop before starting later batches on incomplete child. No retry/replacement/exclusion/pooling or post-result threshold/source change. Runtime metadata is synthetic stream identity, not authority.

Store every input byte array and each unique initial/update packet losslessly inside raw batch JSON. Every measured/warmup output SHA256 binds to the retained bytes; repeated wires must be exactly deterministic. Wall and process-CPU clock endpoints, order, pid/affinity/source freeze and actual subprocess argv/exit/stdout/stderr retained. Audit uses a separate standard-library AIT1 decoder, exact pixels, metadata, dirty counts and raw paired ratio reconstruction; imports no tested encoder/fixture.

Construction:8 unittest methods on distinct tiny RGB/RGBA/L, edge geometry, sparse/full/unchanged, O1 and serialization-failure state. Construction is not a scientific timing sample. Ten fixed controls mutate copies only: condition missing, sample missing, changed input bytes with recomputed packed digest, changed wire sequence with updated per-sample digest, negative clock, missing exit, wrong encoder sequence, wrong dirty count, wrong arm order, incomplete batch. The intact copy must pass first, then each mutation must be effective and rejected. Never run an encoder to rebuild a corrupted result.

## D

Separate gates:

- Integrity/correctness: all18 conditions/270 pairs/three actual exit0 receipts; source/input identities; exact independent initial/update pixel reconstruction in both arms; same metadata/sequence/base; all non-dense wire bytes identical; all10 controls effective and rejected. Missing or unverified evidence is HOLD/STOP; pixel/state contradiction is FAIL_CODEC_CORRECTNESS.
- Benefit: median of nine dense-condition paired wall-time medians <=0.80; each dense median <=0.90; each of six sparse-changed medians <=1.15; every update packet byte ratio <=1.05. Unchanged-path timings are descriptive, not a noisy microsecond regression gate.
- PASS_DENSE_ROUTE_TRADEOFF_SCOPED only if all gates pass; correct complete evidence but benefit miss is HOLD_DENSE_ROUTE_TRADEOFF. Keep unfavorable conditions; do not select a successful subset.

Audit exit0 means integrity verified, NOT that benefit passed. Timing results can only be judged after exact source publication/readback. No threshold or corpus sweep.

## C / U

Candidate includes deferred materialization/order and all-dirty branch; performance is a whole implementation comparison, not isolated causal attribution to zlib. Pure synthetic patterns and technical repetitions do not establish general GUI representativeness, independent workload samples, reliability, tokens, model latency or product readiness. NumPy/zlib/allocator/cache, scheduling/frequency and tiny-frame fixed costs affect timing. Extra dirty-position storage and peak RSS are unmeasured. No guarantee that full wire is near-minimal for unseen images. Same-author independently structured auditor is not external human review. No calibrated combined uncertainty or coverage factor is fabricated.

Primary specifications: NumPy ascontiguousarray (C-order, same content); Python3.13 zlib compress; Python3.13 time perf_counter_ns/process_time_ns. These define operations, not the empirical speedup.

## Variable table and conditional correctness argument

|Symbol|意味|SI単位|定義|範囲・前提|型|
|---|---|---|---|---|---|
|W,H|フレームの幅・高さ|1 (pixel count)|Frame.width,height|正整数|整数スカラー|
|C|画素のチャンネル数|1|RGB:3,RGBA:4,L:1|固定mode|整数スカラー|
|S|タイル辺長|1 (pixel count)|64 in measurement|正整数|整数スカラー|
|N|全タイル数|1|ceil(W/S) ceil(H/S)|有限|整数スカラー|
|D|異なるタイルの個数|1|before/afterの完全比較|0..N|整数スカラー|
|P,Q|前後の画素列|1 (bytes)|長さW H Cの不変byte列|同じgeometry/mode|バイトベクトル|
|B_c,B_d|出力packet長|1 (bytes)|canonical,denseのlen(wire)|正整数|整数スカラー|
|t_0,t_1|壁時計端点|s (raw ns)|perf_counter_ns読み|同じprocess clock|整数スカラー|
|u_0,u_1|CPU時計端点|s (raw ns)|process_time_ns読み|同じprocess clock|整数スカラー|
|T_c,T_d|update壁時間|s (raw ns)|各armのt_1-t_0|正|実数スカラー|
|r|対応試料時間比|1|T_d/T_c|正|実数スカラー|

Case1: incompatible/no base. Both encode Q in a full packet using the same serializer. Decoding returns Q and increments sequence only after serialization succeeds.
Case2: P=Q. Both encode the same empty unchanged packet; ordered receiver retains P=Q.
Case3: P differs and D<N. Both visit exactly the same y-major/x-major tile partition and compare exact uint8 content. Deferred materialization does not change the immutable Q values. Each changed tile contributes the same header and C-order bytes. Thus full and tile alternatives, compression, strict size comparison and tie rule are identical. Decoder replaces precisely the changed tiles, leaving equal tiles from P; output equals Q.
Case4: D=N. Candidate always selects the full alternative already created by canonical. Its decoded pixels equal Q, with identical non-kind metadata. Canonical may select full OR tiles, so byte/minimum-size equivalence is NOT concluded.
In every case the state commit occurs after all required serialization. Failure before commit preserves prior state. This proof assumes ordinary immutable Frame byte storage and deterministic serializer in the pinned environment; source truth, freshness and input authority are separate.

Unit check: W H C counts bytes, no time conversion is hidden; wall intervals and CPU intervals are computed only within their own clocks. r and B_d/B_c are dimensionless and never added to tokens or treated as money.
