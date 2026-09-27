# O2 coalescing composition — #4392

This is a bounded engineering experiment on existing components, not a new queue or codec. Base main: `4c701cc51b06296268ad8d9ae3eff1dd6f2d379d`. Only `research/integration/o2_coalescing_j2c8_v1/` is owned. Related #43/#1008/#1021 and closed #4139 remain unchanged. The prior p6k2 memory/CPU HOLD is not rerun or repaired here.

## H / T / D / C / U

H: selecting source frames before assigning stateful transport sequence/base preserves a decodable selected-frame stream; dropping encoded intermediate packets breaks the consecutive decoder contract. Equal final pixels do not identify the latest source observation.

T: exact unchanged queue contract `404a452aa304b4bde73ec0182450d241e2a744af`, codec `0de27f79e6cbf5ded545430b26a87dcacc142b71`, Frame `d2629bc94d40cc0a8e1bf9e053585549218629ed`. Three compositions: FIFO, ENCODE_THEN_SELECT, SELECT_THEN_ENCODE. Six ordered conditions: SINGLE, CHANGE_BURST, UNCHANGED_BURST, ABA_BURST, TWO_STREAMS, CRITICAL_BURST. Two fresh repeats of each composition in each condition: 36 cases, 72 actual producer/consumer processes. Six immutable batches, one condition each, repetition then mode order. Each stream gets an initial bootstrap before one burst. Actors use pipes, not sockets or GUI input.

Formal L frames are 16 by 12 pixels, 4-pixel tiles. Base is the first 192 bytes of concatenated SHA256 digests of UTF-8 j2c8-0, j2c8-1, etc. Changed step i flips the first i+1 bytes, for i=0,1,2. UNCHANGED never flips; ABA flips on the first two steps then returns to base. TWO_STREAMS interleaves two target/stream scopes. CRITICAL_BURST inserts authored FOCUS_CHANGED and EFFECT_VERIFIED records between frames; these are synthetic labels, not actual focus/effect observations. Exact source identity/content is equal across modes, but outer case IDs and processes differ. Construction uses 8 by 8 frames, separate directories and excluded cases.

D: all 36 rows and six external batch exits must exist. FIFO and SELECT_THEN_ENCODE accept every delivered frame with exact pixels and source metadata. ENCODE_THEN_SELECT accepts SINGLE but refuses the selected burst frame(s) in each of ten other cases, leaving decoder state unchanged. Both selection compositions have identical selection/critical/coalesced IDs. Candidate uses fewer encode calls in burst conditions. All critical records retain source order. No output claims input/replay authority, task success or continuous visual coverage. Raw-only independent auditor must pass and reject at least eight effective copied-record corruptions. Complete unexplained gate miss is FAIL; incomplete provenance/process/raw/source evidence is HOLD/STOP. No model or performance gate.

C: reliable ordered transmission AFTER encoding; immutable source frames; separate encoder/decoder per scope; complete initial bootstrap; exact queue freshness semantics. These conditions do not describe packet loss after selection, reconnect, automatic resync, arbitrary source acquisition, async rates or live critical-event detection. The whole supplied frame sequence is itself discrete, not continuous coverage. The selected stream omits intermediate pictures even if all authored critical records survive.

U: single Linux/CPython/NumPy/zlib environment; no Docker/OrbStack image attestation, model/provider, GUI/native input, external experiment network, user data, installation, timing/CPU/memory/token/task-benefit or production claim. Counters are exact finite accounting, not population rates. Synthetic timestamps have no measured physical-age uncertainty; no calibrated combined uncertainty or coverage factor is invented. Same-author separate audit implementation/process is not external review.

## Variable / field table

| Field | Meaning (Japanese) | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| sequence | 転送連番 | 1 | Successful encodes/accepts within one stream, nonnegative integer | scalar integer |
| base | 参照する直前の転送連番 | 1 | Encoder sequence before successful serialization; nonnegative integer | scalar integer |
| event_id | 元観測の識別子 | not applicable | Unique source record identifier, unchanged by encoding | string |
| seq | 元記録の順序 | 1 | Strictly increasing within the authored batch | scalar integer |
| t_ns, observed_ns | 元観測の論理時刻 | s, encoded as ns | Synthetic 1000000+1000*seq; copied exactly to codec metadata | scalar integer |
| now_ns, max_age_ns | 選別基準時刻・最大年齢 | s, encoded as ns | Same logical clock; nonnegative integers; not physical deadlines | scalar integer |
| width,height,tile_size | 画像・タイル寸法 | 1 (pixel counts) | Positive integers, L mode one byte per pixel | scalar integers |
| pixels | 画素データ | 1 (byte values) | Immutable bytes, length width*height for L; retained in hex | byte vector |
| encoded,delivered,refused | 符号化・配達・拒否件数 | 1 | Counts of actual recorded function results/messages | scalar integers |
| start_ns,end_ns | 実プロセス観測時刻 | s, encoded as ns | Same-host monotonic diagnostics only | scalar integers |

Unit check: subtract only logical times from the same logical clock for queue age. No logical time is subtracted from process monotonic timestamps. Transport/source sequences are dimensionless counts, never clocks. L payload length counts width*height bytes, not elapsed time.

## Conditional argument, with no omitted step

Initially both codec ends have sequence zero and no base. Encoding and delivering one bootstrap succeeds and gives both identical frame and sequence one. Assume after a delivered selected frame both ends have identical frame and sequence. Source selection does not call the encoder for discarded frames, so it cannot change the encoder base. Encoding the next selected frame uses the identical prior base and the next sequence. Its full packet, unchanged reference, or exact changed tiles reconstruct the selected frame under the unchanged codec contract. Ordered delivery makes the receiver's base/expected sequence agree. Successful acceptance commits the same new frame and sequence. Induction establishes selected-frame decodability for every finite selected subsequence under the stated transport assumptions.

In contrast, encoding at least one omitted frame increments the sender sequence. If the next retained packet follows that omission without a reset or delivery of the missing packet, its base or sequence differs from the receiver's expected pair. The unchanged decoder checks that pair before publishing pixels or metadata, so it refuses, leaving the last accepted state. This remains true when the packet is full or pixels equal the earlier base: the actual protocol checks sequence before its packet-kind branch. No metadata renumbering or implicit resync is introduced.

Source event_id and observed_ns are copied from each chosen source, not generated from transport sequence. Consecutive transport sequence therefore proves only selected transport continuity, not capture continuity. In ABA, base and final pixels coincide while intermediate images differ; refusing or accepting the final source identity must not be inferred from pixel equality. Critical ID retention is a separate exact stream, not reconstruction of discarded images.

ERROR CHECK: claims require no post-encode loss, no cross-scope codec sharing and immutable inputs. The proof says nothing about latest-at-display or task success. FIFO covers all supplied discrete frames only.

## Execution and first-outcome retention

Construction v0 retained nine cases; self-review found unequal cross-mode source IDs and an unjustified continuous-coverage label. Both original sources and raw outputs stay in construction/. Corrected construction_v1 contains nine new excluded cases and new controls. These are prefreeze engineering corrections, not formal retries.

Publish readable source, plan, environment and FREEZE.json; verify Git identities before any formal case. Run `python -B launch.py formal 0` through batch5 once each. Child communicate bound5 seconds, batch supervisor30 seconds; initial process creation is not a hard-real-time bound. Exclusive destination prevents reuse; previous batch must have a successful external exit. Any incomplete batch stops the allocation. Run `python -B audit.py . formal` and `python -B audit.py . formal --controls` afterward. Audit only during review; do not rerun consumed formal batches.

Record every stdin/stdout/stderr/argv/PID/exit, initial/burst source bytes, generated/discarded/selected packet bytes, codec states, queue sidecar, source hashes and actual batch outcomes. Serialization in JSON/hex is reversible and not a model-token measurement. All substantive raw data must be delivered, not replaced by counts.

Background: GStreamer queue documentation (https://gstreamer.freedesktop.org/documentation/coreelements/queue.html) documents optional old/new buffer drops. GStreamer is NOT executed. Python3.13 subprocess documentation defines communicate/wait behavior. Scientific support is the pinned repository code and retained experiment.
