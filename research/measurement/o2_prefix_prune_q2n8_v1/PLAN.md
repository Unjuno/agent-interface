# O2 compressed-prefix pruning — q2n8

Status at writing: no measured corpus update has run. This is a prospective LOCAL
engineering allocation, not public GitHub preregistration. No existing Issue is
claimed or completed. Proposed successor to #4139/#4340; #4362 owns a different
streaming-memory comparison and is not rerun. The previous b7f3 construction and
STOP remain immutable. Only its two exact canonical source files are reused.

## Purpose -> needed capability -> current position -> route

Purpose: reduce wasted encoding work without changing selected AIT1 packets.
Needed capability: a sound lower bound on a candidate packet's final size.
Current position: canonical O2 always builds/compresses full and tiles; full wins
ties. Test only exact incumbent pruning, not the all-dirty heuristic or a new
memory-staging claim. Route: proof -> small construction -> local freeze -> one
18-condition block -> independent raw audit/control -> evidence handoff.

## H / T / D / C / U

H: stopping tile materialization/compression only when its emitted compressed
prefix plus exact tile-header length already reaches the full-packet size retains
the minimum-size output and can save enough work to reduce encoding time.

T: supplied Linux/CPython/NumPy/zlib container, one available logical CPU, no
frequency lock, batch one image. Three arms: CANONICAL, STREAM and PRUNED. STREAM
and PRUNED use the identical PrefixEncoder source with only a boolean parameter
changed. They both first determine all dirty coordinates so the exact metadata
count and last.changed_tiles remain known. Both always encode the full candidate.
The canonical contrast additionally changes detection/staging and compression
API; do NOT attribute all differences against it to pruning.

Exactly 320x240, 640x480, 1025x769 RGB8, each with UNCHANGED, SPARSE,
DENSE_SOLID, DENSE_NOISE, DENSE_ROW_REPEAT, DENSE_TILE_REPEAT: 18 conditions.
SPARSE changes an 8x8 bottom-right patch. ROW_REPEAT repeats seven independently
pseudo-random rows. TILE_REPEAT repeats one 64x64 pseudo-random tile. Others are
literal neutral/solid/random bytes. These are directed synthetic inputs, not
held-out GUI frames or a natural-workload sample. Recipes/seeds are fixed in
corpus.py and every byte/hash is saved before timing.

Per condition: two excluded warmup triples, then 15 timed triples. Rotate through
all six arm permutations, fixed by condition/sample index. 270 timed triples =
810 timed update encodes; 36 warmup triples =108 warmup update encodes. Every update
gets a freshly initialized encoder and an untimed first-frame encode. Input
construction/loading, initial encode, hashing and output recording are outside
the update timer in ALL arms. Measure wall and process CPU brackets; primary gate
uses each paired PRUNED/STREAM wall ratio, not ratio of separate time medians.
No tracemalloc/RSS performance claim is made by this allocation.

Each condition is executed once by an exclusive-create child process, 25-second
safety timeout. Three fixed outer command groups of six conditions; all IDs are
exclusive. Any incomplete/nonzero condition stops the allocation. No retries,
substitutions, post-result exclusions, extension, parameter tuning or old-result
pooling. Retain actual stdout/stderr/argv/PID/exits and every timing/warmup sample.

D: contract evidence requires all 18 complete conditions, unchanged source/input
hashes, exact initial/update packets versus canonical independent assembly,
exact output pixel content by raw-payload reconstruction, same sequence/base,
metadata and completed state, source-bound processes and 12 effective auditor
mutations. Resource benefit requires at least TWO changed conditions with both
median paired PRUNED/STREAM wall ratio <=0.90 and tile bytes fed <=0.80 of STREAM,
plus every changed condition's median time ratio <=1.15. If complete and correct
but the benefit gate fails: HOLD_LOCAL_PRUNING_TRADEOFF. PASS is only
PASS_LOCAL_EXACT_PREFIX_PRUNING; public qualification remains pending.
Any integrity failure: HOLD_AUDIT/STOP; interpret an actual semantic/wire mismatch
separately, never call it a speed win. The analysis script's exit0 means completed
analysis, NOT automatic hypothesis PASS.

C: append-only emitted outputs make the lower bound valid, but zlib may buffer
most output until final flush. Prefix length may therefore reveal domination too
late. Header-only domination can avoid tiny tile candidates. Per-tile branching,
Python dispatch and staging overhead can erase saved work. Input compressibility
and tile order are deliberately varied; no result-driven scenario change.

U: 15 technical repetitions in one shared container are not 15 independent GUI
workloads. CPU affinity is not host exclusivity. No calibrated combined standard
uncertainty u_c or coverage factor k is available; neither is invented. Report
median/range, not population reliability or hard timing guarantees. No model,
provider, GUI/task input, package installation or experiment network activity.
No Docker/OrbStack image attestation, arbitrary-app/token/bandwidth/end-to-end
benefit, production default or full-roadmap completion follows. Separate auditor
is same-author separate code/process, not outside human review.

## Variable table

| Symbol | Japanese meaning | SI/unit | Definition | Domain/assumptions | Type |
|---|---|---|---|---|---|
| H | 差分パケットの固定ヘッダ長 | SI 1; byte count (1 byte=8 bits) | len(AIT1 prefix + exact JSON metadata) | nonnegative integer, final count fixed | scalar integer |
| F | 全画像パケット長 | SI 1; byte count | len(completed full packet) | positive integer | scalar integer |
| j | 処理済みタイル数 | 1 | completed tile feeds | nonnegative integer, raster order | scalar integer |
| C_j | 圧縮器が既に返したバイト数 | SI 1; byte count | sum of emitted chunk lengths after j tiles | nonnegative, append-only | scalar integer |
| R_j | 以降に返る残りバイト数 | SI 1; byte count | future compress + final flush lengths | nonnegative if compression completes | scalar integer |
| L | 完成した差分パケット長 | SI 1; byte count | H+C_j+R_j | successful complete stream | scalar integer |
| t_P,t_S | 打切りあり・なしの更新時間 | s, recorded ns | end-start on same monotonic timer | strictly positive | scalar real |
| r | 対にした時間比 | 1 | t_P/t_S | positive | scalar real |

## Complete conditional proof

1. Exact dirty detection finishes before compression, fixing all tile coordinates,
   their raster order, count and tile-header bytes. Therefore H is fixed.
2. A streaming compression call returns a bytes object that must be concatenated
   to earlier output. The final flush appends remaining output. Earlier bytes
   cannot be retracted. Thus C_j and R_j are nonnegative byte counts and
   L = H + C_j + R_j >= H + C_j.
3. If H+C_j >= F, step 2 gives L>=F. Canonical choice requires the tile packet to
   be STRICTLY shorter than full. A tie also chooses full. Thus abandoning this
   candidate and returning full does not change the choice against the completed
   STREAM candidate. Checking at equality is necessary to preserve the tie rule.
4. If H+C_j<F at all inspected boundaries, no pruning occurs. Exactly the same
   tile headers/pixels, same compressor parameters and final flush are evaluated
   in STREAM and PRUNED, hence their chosen packet is identical.
5. Initial/incompatible/O1 and exact-unchanged paths bypass tile pruning and call
   the same canonical packet function, so their bytes are also identical.
6. The implementation updates previous/sequence/last only after a selected packet
   is fully serialized. Exceptions in any evaluated step before that point leave
   these fields unchanged. Skipping a dominated suffix can avoid exceptions or
   allocations that STREAM would have encountered; UNIVERSAL exception-trace
   equivalence is NOT claimed. Inputs are trusted bounded immutable valid frames.
7. One-shot canonical zlib output versus chunked zlib output is an additional
   empirical compatibility gate, not implied by equal decompressed pixels.
   The independent auditor rebuilds BOTH candidate packets with one-shot zlib,
   checks each stored selected packet, and separately checks stream byte parity.
   The theorem in steps 1-6 is unconditional only relative to the completed
   STREAM candidate under its stated successful append-only contract.

Dimensional check: H,C_j,R_j,F,L are all byte counts, so addition and comparison
are dimensionally valid. r divides two durations in seconds (or both in ns), so
it is dimensionless. Example: H=220,C_j=800,F=1000 gives L>=1020, so tile cannot
win; H=220,C_j=780 is an exact tie bound and likewise full must win. No bound is
claimed when H=220,C_j=779: remaining bytes could still determine the winner.

### ERROR CHECK (proof)

The rule uses EMITTED bytes, not bytes submitted to zlib; pending internal output
is not treated as negative or already observed. No intermediate flush is added.
No assumption that all dirty tiles imply full is smallest. All dirty positions
are still discovered, so the optimization cannot claim skipped comparison cost.
The proof preserves selected bytes only subject to the separately tested
canonical/stream wire-identity gate, not all zlib versions or error paths.

## Primary implementation references

Canonical repository main 4c701cc51b06296268ad8d9ae3eff1dd6f2d379d:
- research/observation_tiles/tile_transport.py Git blob 0de27f79e6cbf5ded545430b26a87dcacc142b71
- research/observation_gating/exact_gate.py Git blob d2629bc94d40cc0a8e1bf9e053585549218629ed
- Python 3.13 zlib documentation, Compress.compress / Compress.flush:
  https://docs.python.org/3.13/library/zlib.html
- zlib manual, stream output and flush semantics: https://www.zlib.net/manual.html
  Consulted 2026-09-26; actual installed versions are frozen in ENVIRONMENT.json.

## Integration and publication gates

Local pass/hold -> complete original evidence -> read-only restoration -> unposted
Issue/PR proposal -> permitted GitHub publication/readback -> applicable exact-head
CI and review -> only then qualified main integration. The currently exposed
GitHub connector contains no write operations; gh is absent and direct GitHub DNS
fails. Public source-first preregistration is NOT claimed. No blocked predecessor
content is republished or routed around a tool restriction. Our new source is a
clean implementation; only the two unblocked canonical files are reused.

## Cross-domain interpretation

Algorithm engineering: incumbent lower bounds can avoid candidates without
changing a minimum. Compression systems: internal output buffering limits usable
prefix bounds. Experimental metrology: paired times isolate the boolean factor,
while lineage and environmental scope limit transfer. These are transfer ideas,
not empirical results in three separate domains.
