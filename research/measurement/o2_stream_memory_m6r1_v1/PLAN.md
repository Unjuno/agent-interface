# #4362 — streaming O2 tile memory, m6r1

## Purpose and roadmap

Test a single new storage strategy after closed #4139, not repeat its contiguous-copy timing. Exact reference main is 4a1f3957e91b412a64769199f78f2c4b0102d28b. The exact canonical O2 is copied without modifying any upstream/runtime file. #4340 independently owns skipping dense tile compression; this study always computes both alternatives and preserves minimum packet selection. #4197 remains historical wrapper evidence; this allocation neither depends on nor replays its input experiment.

Roadmap: source identity -> disjoint small construction -> public source/input/gate freeze and readback -> 12 one-shot child conditions -> raw-only audit/10 controls -> complete additive evidence PR -> exact-head CI/review -> qualified merge/readback. No global ROADMAP completion follows.

## H / T / D / C / U

**H.** Streaming the ordered dirty tile headers/pixels through one compressor reduces temporary traced peak memory without changing AIT1 bytes or changing the returned-frame contract. Dense memory ratios must each be at most 0.75, their six-condition median at most 0.65. Each non-dense candidate peak must be at most 1.20 times baseline plus 32768 bytes. Each changed-condition median paired uninstrumented update-wall ratio must be at most 1.20. These are selection thresholds, not estimated physical constants.

**T.** RGB8 at 319x239, 1023x767, 1537x1025, each with UNCHANGED/SPARSE/DENSE_SOLID/DENSE_TEXTURE. Tile edge64, zlib1, DEFLATED, wbits15, memLevel8, default strategy, no dictionary/intermediate flush; terminal Z_FINISH. Use exact stored raw inputs, not resampled images. Corpus is deterministic periodic texture, not independent random noise, held-out GUI data or representative prevalence. Every dense tile differs from its base; sparse changes one center pixel's first channel. One fresh child per condition. Two retained-but-excluded warmup pairs,11 timed pairs with tracing OFF,3 memory pairs with tracing ON, alternating canonical/streaming by condition+pair parity. Formal132 timed pairs,36 memory pairs,24 warmup pairs:384 update calls total. Base encoding is outside all update measurements. No exclusion/replacement/retry, no formal evaluation before public freeze. Stop on any incomplete process/condition; keep partial files.

Time is sampled around encode with perf_counter_ns and process_time_ns; the wall bracket includes clock-call overhead. Memory tracing starts only after input/base allocation, with one traceback frame and reset_peak. It captures temporary allocations and the returned output, not the preloaded raw inputs. Time samples under tracing are diagnostic only. resource.ru_maxrss before/after is process-lifetime high-water across arms, not an isolated update peak or whole-process delta attributable to the candidate.

**D.** Complete source/process/data integrity plus exact packet/pixel/state parity and all resource gates yields PASS_STREAMING_O2_MEMORY_SCOPED. Pixel/state mismatch -> FAIL_CODEC_CORRECTNESS. Correct decoded data but wire mismatch -> HOLD_WIRE_PARITY. Complete exact result missing memory/time selection gates -> HOLD_MEMORY_TRADEOFF. Missing rows/source/receipts/controls -> HOLD/STOP. Auditor uses independent stdlib row slicing/packet encoding/decoding, never imports candidate/baseline/runner/NumPy. Corruptions are tested on copies, must actually change bytes and produce integrity errors rather than a parser exception/no-op. Same author, different implementation/process: not independent human review.

**C.** The candidate retains full alternative and compressed tile output. Compressor state, output-copy overhead and extra Python/zlib calls can dominate small/sparse/unchanged inputs. Low compression and larger output may erase the memory saving. Memory tracing changes execution cost; therefore it is separated from timing. No policy selects an arm based on expected labels.

**U.** One machine, nonexclusive shared CPU, unpinned clock, known synthetic periodic inputs and technical repetitions. No natural variance/reliability, whole-process peak RSS, hard memory bound, cross-zlib compressed-byte theorem, GUI/capture/IPC/model/task/token/latency improvement, production change or human-tempo claim. No calibrated combined standard uncertainty or coverage factor exists for this allocation; u_c and k are not estimated. Ratios/ranges describe only retained samples.

## Variable table and units

|Symbol|Meaning / 日本語|SI / information unit|Definition|Domain / assumptions|Type|
|---|---|---|---|---|---|
|W,H|画像の幅・高さ|1 (pixel counts)|frame geometry|positive integers,RGB8|integer scalars|
|c|画素当たりチャネル数|1|3 for RGB8|here3,construction also1/4|integer scalar|
|B|元画像の保存量|byte (8bit,not SI base)|W*H*c|uint8 bytes|integer scalar|
|K|変更タイル数|1|exact dirty-tile count|0..ceil(W/64)*ceil(H/64)|integer scalar|
|U|変更タイル列の未圧縮量|byte|sum over changed tiles of16+tile width*tile height*c|16-byte canonical header|integer scalar|
|Z|圧縮されたタイル列の長さ|byte|compressed output length|nonnegative integer|integer scalar|
|S|圧縮器内部の作業量|byte|implementation-dependent compressor working memory|fixed settings,not fully independently measured|scalar|
|F|全画面パケット長|byte|full alternative length|canonical compression/header|integer scalar|
|P_a,j|計測された一時traced peak|byte|traced peak minus pre-update traced current for arm a, repetition j|not RSS,three observations per arm|integer scalar|
|t_a,j|更新符号化の壁時計時間|s|recorded ns difference times10^-9|11 uninstrumented pairs|positive scalar|
|R_P|条件別メモリ比|1|median(P_stream,j)/median(P_canonical,j)|denominator positive|real scalar|
|R_t|条件別時間比|1|median over j of t_stream,j/t_canonical,j|paired order retained|real scalar|

Dimensional check: W,H,c are counts and each uint8 contributes one byte, so B and U have information-size units. Subtracting two ns timestamps then scaling10^-9 gives seconds. Time/time and bytes/bytes ratios are dimensionless. The non-dense slack32768 is bytes; it is not added to a dimensionless ratio. Example: a full64x64 RGB tile has12288 data bytes plus16 header bytes=12304 bytes. This is a payload bound only, not peak RSS.

## Derivation and conditional equivalence proof

1. Both encoders obtain identical read-only uint8 arrays from the exact same immutable before/after bytes and geometry. Identical loop limits enumerate tiles row-major. Both compare each same pair with np.array_equal. Thus each chooses the identical ordered dirty set and identical K.
2. For each dirty tile, both produce the identical16-byte network-order x,y,width,height header and the identical C-order pixel byte sequence. The candidate uses the same np.ascontiguousarray(...).tobytes() expression as canonical. It does not approximate, omit or reorder pixels.
3. Canonical concatenates this ordered sequence before compression. Streaming presents its identical segments, in the same order, to a single compressor, finishes once and emits all outputs in order. Thus its decompressed tile sequence must equal the canonical uncompressed tile sequence under the zlib codec contract. This is a lossless-content result, NOT a proof of compressed-byte equality across arbitrary zlib implementations, settings or intermediate flush choices. This experiment separately requires exact bytes against an independently reconstructed canonical packet.
4. Both build the same metadata after K is known. If the compressed tile bytes are also equal on this exact build, the complete tile packet is equal. Full packets are computed with the unchanged canonical packet() call in both. Therefore comparing their lengths with the same strict-less-than rule yields the same route and packet, including ties. Unchanged/cold/resize/O1 routes are unchanged calls.
5. No candidate assignment to previous/sequence/last occurs until after all serialization/compression/packet-selection operations return successfully. A failure earlier leaves those three fields unchanged. Construction forces compressor creation, compressor finish and metadata failures and checks this state against its pre-call snapshot. This proves the source-level commit placement, subject to ordinary single-threaded immutable-input operation; concurrent mutation/reentrancy is excluded.
6. Canonical holds approximately U bytes in pieces plus another U-byte join during compression, as well as object overhead, F and Z. Candidate no longer retains those two uncompressed collections; it holds one bounded tile materialization, S, F and accumulated compressed output (and transient copies). This explains a possible peak reduction but not a universal numeric bound: Z, compressor internals, allocator policy and untraced blocks remain implementation/workload dependent. The memory and speed gates therefore require measurement, not asymptotic inference alone.

## Primary references

Python3.13 zlib documentation: https://docs.python.org/3.13/library/zlib.html
Python3.13 tracemalloc documentation: https://docs.python.org/3.13/library/tracemalloc.html
zlib1.3.1 manual: https://www.zlib.net/manual.html
Repository source pin and parent #4139 are in BASELINE.json and the Issue. Documentation describes APIs, not the measured outcome.

## ERROR CHECK

No compression-ratio or runtime-performance theorem is substituted for data. Wire parity is stricter than decoded-content parity. Traced peak is explicitly not whole-process RSS. Two technical-repetition phases remain separate; all formal condition IDs have one consumed process receipt. Scientific and publication/CI outcomes stay separate.
