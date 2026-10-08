# PNG preparation versus decoded delivery: q7n2 / Issue 4401

## Frozen scientific scope

Parent evidence: `research/observation_tiles/IMAGE_ARTIFACT.md` at main
4c701cc51b06296268ad8d9ae3eff1dd6f2d379d (blob ad0aa882d4d7f03d577ac6becdb945f5b6567d7d).
That study times preparation, not transfer/decode. This experiment is a different
measured boundary, not a repetition of its GUI tasks or cache studies. The
previous stream-verifier package remains under #4087 and is not imported or
republished. Its operation-specific publication STOP is preserved.

H: level1's encoding advantage can reverse at decoded acknowledgement when its
larger PNG is carried by an explicitly constrained byte service.
T: three frozen, development-known Tk screenshots, 800x480, RGB; level1/6, reuse
false; ordinary pipe versus paced65536 bytes/s;4096-byte chunks; three paired
repetitions per stratum. Six sequential blocks, six rows each, exactly36 rows.
Receiver is a separate Python process. Image/plugin and process startup are
outside the measured interval. File generation/read, payload transfer, consumer
decode/hash/ACK are inside. Receiver writes its retained PNG after ACK.

D: all36 rows/18 pairs/six observed outer exits, source/corpus/pixel checks and
at least8 effective corruption controls must pass. At least two families must
have pooled paired median encode(level1)/encode(level6)<=0.90 AND paced paired
median total(level1)/total(level6)>=1.10, with strictly larger level1 PNGs.
Otherwise complete integrity yields HOLD_NO_DELIVERY_RANKING_DISCRIMINATOR.
Wrong pixels/accounting yields FAIL; missing source/process evidence yields
HOLD/STOP. Fast-pipe winner is descriptive. No optional stopping, replacement,
retry, pooled transport distribution or post-result gate adjustment.

C: the capped service is controlled emulation, not actual network throughput.
The screenshot corpus is historical during timing; no freshness/action claim.
One toolkit is not three independent applications. No fsync, model, token,
public-runtime, input, cold-cache or broad human-tempo claim. A rank reversal
would not recommend a global compression default.
U: three technical repetitions per stratum, unpinned frequency/shared load,
source image content and OS scheduling; descriptive median/min/max only.
No calibrated combined standard uncertainty or coverage factor is invented.

## Measurement definitions and variable table

| Symbol | Meaning (Japanese) | SI unit | Definition/domain | Type |
|---|---|---|---|---|
| t0 | 公開開始時刻 | s | sender monotonic start_ns / 1e9 | scalar |
| tp | PNG公開完了時刻 | s | prepared_ns / 1e9, tp>=t0 | scalar |
| ta | 復号応答受信時刻 | s | ack_ns / 1e9, ta>=tp | scalar |
| E | 符号化・公開時間 | s | tp-t0, nonnegative | scalar |
| W | 復号応答までの全時間 | s | ta-t0, nonnegative | scalar |
| S | PNGのバイト数 | 1 | positive integer byte count | scalar |
| B | 診断用転送速度 | s^-1 | bytes per second; positive for paced arm | scalar |
| O | 残りの局所費用 | s | ideal serial model's non-encoder/non-transfer cost | scalar |
| j | 圧縮レベル | 1 | j in {1,6}; subscripts select arm | scalar index |

Thus E=tp-t0 and W=ta-t0. Clock differences are within a single sender; receiver
brackets are same-container monotonic diagnostics. No subtraction of X11 server
event milliseconds from host nanoseconds. Inner sink time is included in E,
never added to it again. Overlapping transfer/decode/ACK intervals are not summed
as independent elapsed components.

Conditional analytical motivation ONLY: an ideal serial byte service has
W_j=E_j+S_j/B+O_j. Subtract the two identities to obtain
W_1-W_6=(E_1-E_6)+(S_1-S_6)/B+(O_1-O_6). If O_1=O_6,
E_1<E_6, and S_1>S_6, the larger-byte arm is slower exactly when
B<(S_1-S_6)/(E_6-E_1). This follows by moving the negative encoder difference
and multiplying by positive B; no inequality direction changes. Units check:
byte count divided by byte count/s gives s; the threshold has byte count/s.
This is NOT an identification claim for measured pipes: O and scheduling vary.
The experiment records actual elapsed W and does not impute it from this model.

## Construction and custody

Private TCP-disabled Xvfb collection completed and server exit0/socket absent
are retained. No task input was injected. Capture normalization uses declared
24-bit TrueColor,32bpp,LSBFirst masks; original X padding bytes are retained,
not assumed zero. All captured RGB files are byte-bound before timing.

Excluded attempt01 found a TEST efficacy-assertion defect: Python equality
considers False equal to0. The auditor already rejected Boolean exits. Preserve
old test/diagnostic. Its TemporaryDirectory raw was cleaned by the test and is
not claimed retained. Attempt02 uses JSON-byte inequality, synchronizes modified
ACK wires, and retains both small pipe deliveries. Three methods,12 semantic
mutations and a CRC mutation pass. No scored timing was used to select gates.

## Run protocol

Publish/read back every source file and the exact corpus-hash FREEZE before
formal. Full corpus bytes are retained locally and accompany final evidence.
For i=0..5 run `python -B supervise.py i FREEZE_SHA256` once, sequentially.
The preceding block's actual exit must be0. Each block has30s subprocess limit
under a45s outer tool envelope. The collector persists any first STOP; do not
advance past an incomplete block. Run raw-only `python -S -B audit.py PATH`
and effective copied-record controls separately after collection.

Roadmap: construction -> public source/gate freeze -> six blocks -> raw audit
and controls -> complete additive PR -> applicable CI/scoped review -> qualified
research-only main merge/readback -> supported dependency-safe own-ref cleanup.
Global ROADMAP and model delivery/utility requirements are not completed here.
