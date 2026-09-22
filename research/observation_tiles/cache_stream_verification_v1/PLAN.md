# Bounded full-byte PNG verification: known length versus chunk buffer

## Chronology, scientific question and decision

Allocation `cache-stream-verification-4029-20260922-01`. This is a NEW, locally
preregistered experiment, not a rerun of #4029 or the preceding chat-local
`cache-size-reuse-4029-20260922-01`. No GitHub Issue or branch has been created:
this session's discovered 48 GitHub actions are read-only; plugin discovery
returned the same installed connector; gh and GitHub auth environment variables
are absent. This local availability observation is not a fleet-wide blocker.
An eventual Issue must disclose retrospective GitHub publication.

Closed #4029 supplies the unchanged original sink and BYTE_PIN_REPAIR comparator.
Its finite maintenance result remains valid. The preceding new-size experiment
exposed repeated regeneration of valid PNGs larger than 262144 encoded bytes.
This question changes the verification implementation and support envelope:
can a bounded known-length byte verifier preserve maintenance correctness and
reuse larger images, while a reusable 65536-byte buffer avoids the full-read
allocation? This is a practical candidate comparison, not a new hashing theorem.
The concrete #2979/#3370/#2789 observation-artifact decision is whether to advance
this scoped verifier to an actual image-delivery integration evaluation.
Do not promote it into runtime or claim end-to-end model benefit here.

## H

H1: FULL_PIN and STREAM_PIN accept unchanged valid larger artifacts and regenerate
missing, truncated, appended, changed-tail and losslessly re-encoded cache files
through the byte-identical sink. They preserve changed-frame publication and
exclusive-create collision refusal. They perform identical byte-pin decisions.
The legacy 256KiB comparator still regenerates every warm overcap artifact.

H2: in each of the two above-256KiB strata, median of five paired ratios of
STREAM_PIN/LEGACY_256K total wall time for eight unchanged warm publications is
at most 0.50. This is a scoped local performance threshold, not a production
promise; a complete miss is HOLD_LOCAL_TIME, without tuning.

H3: for the 640x480 high-complexity input, STREAM_PIN's separately measured
tracemalloc peak for one inspection is at most 196608 bytes in all five cases,
and its median paired peak ratio to FULL_PIN is at most 0.25. This measures
traced allocations during validation only, not process RSS, whole-frame memory,
Pillow native allocations, filesystem cache, or total application memory.

## T

Provided Linux x86_64 container; actual version, executable identity, Pillow,
OpenSSL, zlib, CPU/cgroup and clock identities are in ENVIRONMENT.json. CPython
3.13.5, Pillow12.3.0, OpenSSL3.5.5, zlib1.3.1. No Docker/OrbStack engine/image
attestation, install, model/provider, GUI/input, credentials, user files or
experimental network. Only private generated RGB/PNG files are used.

Three policies:
1. LEGACY_256K: complete unmodified #4029 Candidate, BYTE_PIN_REPAIR.
2. FULL_PIN: register encoded length and SHA256 of each newly produced file;
   on reuse require same current Frame, same length, and whole-file digest.
3. STREAM_PIN: exactly the FULL_PIN contract but readinto a reusable 65536-byte
   buffer and hash every returned byte. Both new policies enforce an independent
   maximum encoded support size of 4194304 bytes. Unsupported registration
   raises and is not a successful publication. No support claim above that cap.

Performance: three independently generated SHAKE256 RGB images (256x256,
320x320,640x480), three policies, five repetitions:45 fresh worker processes.
Each publishes once then eight times with fresh equal immutable Frame bytes.
Five immutable nine-case batches, one repetition each. Policy order rotates
with image/repetition. Warm-up registers Pillow plugins and reads fixture bytes;
no scored publish is discarded. Initial acquisition/pinning is retained and
reported separately. Every outer publish clock includes validation, sink work,
registration and receipt construction. Input copying, snapshots, source checks,
imports, process start and journal serialization are outside those intervals.
Snapshots warm the local file cache in every arm; no cold-storage claim.

After each new-policy performance case: one separately prescribed read-only
instrumented cache inspection records every requested/received read length;
then a separate tracemalloc inspection (no read-segment list) measures validation
allocations. Neither is counted as one of the eight timed publications.
Both must preserve file bytes and the exact original pin. This is explicitly
planned instrumentation, not unreported retry or duplicated formal timing.

Maintenance: noise640 only; seven conditions (MISSING, TRUNCATED, TAIL_CHANGED,
LOSSLESS_REENCODE, FRAME_CHANGED, NEXT_NAME_OCCUPIED, APPENDED), three policies,
two repetitions:42 fresh workers in two immutable21-case batches. Initial
publish -> completed declared maintenance -> post-maintenance publish -> one
steady follow-up, except collision stops at its expected refusal. Corruption is
cooperative, in owned bounded files, not a security exploit or hostile decoder
study. A tail byte beyond262144 changes without changing length. Re-encoding at
PNG compression0 changes bytes but preserves pixels; all byte-pin policies must
regenerate it. Frame change alters one input byte. The occupied next output name
contains an exact sentinel that must remain unchanged.

Total87 cases, seven batches,525 attempted publications (six expected collision
refusals and519 successful returns). Each worker has an8-second bound. Each
external batch communicate has a30-second bound plus at most3 seconds kill/reap
cleanup; no next batch after a missing or nonzero exit. Tool envelope40 seconds
per invocation. No background/detached work. Source, environment, fixtures,
schedule, tests, auditor and this plan are hash-frozen before the first batch.
Original first outcomes are immutable: no retry, case replacement, exclusion,
pooling or post-freeze tuning. A setup/collector/publication problem stays with
this question and does not create another supervisor research chain.

## D

PASS_STREAMING_REUSE_CONTRACT_SCOPED only with all87 expected rows,525 attempted
publications, exact output pixels and file histories, complete source/identity/
actual child+outer exit records, full-byte inspection accounting, raw-only audit
and12 semantic corruption controls rejected. H2 and H3 have separate decisions.
A scientific contradiction with complete evidence is FAIL; missing source,
process, time envelope or raw evidence is HOLD/STOP, never inferred completion.
Every failed or partially completed case is preserved. Read-only re-audits are
allowed and must be identified; they do not recover an unobserved exit.

Independent audit means a separate implementation/process by the same author,
not an external reviewer. The auditor imports neither Candidate, GuardedSink,
Pillow nor measurement helpers; it independently decodes retained RGB8 PNGs,
recomputes byte pins/decisions, verifies all file histories and derives timings.
Blob hashes are validated before cached decoding. Invalid cached files need not
be valid PNGs, but every successful returned artifact must decode to the exact
current requested Frame. Historical changed files stay retained as evidence.

## C / implementation assumptions

Single cooperating owner, quiescent regular files throughout each inspection
and reuse, trusted private current Frame and successful original PNG generation.
Readback length and digest are integrity checks, not authentication. Hash
collision resistance is an assumption for general use; in this finite corpus
all returned pixels are independently compared exactly. Length-only acceptance
is forbidden; same-length tail changes test that distinction.

No lock, atomic snapshot, concurrent writer, pathname-replacement-after-check,
permission failure, network filesystem, power loss, restart durability, arbitrary
image mode or malformed-codec protection is established. Ordinary file I/O can
block; bounded byte work is not a hard wall-clock deadline. Image data already
exists in memory; chunking only changes validation's auxiliary buffer.
FULL_PIN controls whether the gain is simply removing regeneration; any stronger
claim that chunking itself accelerates hashing would need its own timing result.
Frame equality and cache integrity do not grant source currentness, model
presentation/consumption, input authority, task success or event-history coverage.

## Variables / units / conditional argument

| Symbol | 日本語の意味 | 単位（SIとの関係） | 定義 | 定義域・前提 | 型 |
|---|---|---|---|---|---|
| N | 登録済みPNG長 | byte（8 bit、SI物理量ではない） | 生成後に記録したファイル長 | 整数、1..M | 整数スカラー |
| M | 対応する最大PNG長 | byte | 4194304 | 正の固定整数 | 整数スカラー |
| B | 作業バッファ上限 | byte | 65536 | 正の固定整数 | 整数スカラー |
| r | 未読バイト数 | byte | 初期N、読取後に減少 | 0..N | 整数スカラー |
| q | 各読出し要求長 | byte | min(B,r) | 1..B、r>0 | 整数スカラー |
| d | 実際の読取長 | byte | readinto戻り値 | 0..q | 整数スカラー |
| H | 累積ハッシュ状態 | なし | 読み取った接頭辞のSHA256状態 | hash.updateの規約 | 状態オブジェクト |
| t_s,t_e | 呼出し前後時刻 | s（記録はns） | 同一workerの単調時計 | t_e>=t_s | 整数時刻スカラー |
| W | 8回の公開合計時間 | s（記録はns） | sum(t_e-t_s) | 非負、同一case | 実数スカラー |
| P | traced割当ピーク | byte | tracemalloc.get_traced_memoryのpeak | 検証区間だけ | 整数スカラー |

Conditional proof: initially r=N and H is the empty hash. At each iteration,
q=min(B,r), and 0<d<=q must be read or the operation refuses. Updating H with
exactly those d bytes preserves the invariant that H hashes precisely the
already-read prefix, while r decreases by d. Hence the loop has at most N
iterations (normally ceil(N/B)), cannot read more than N data bytes, and reaches
r=0 only after the complete N-byte content was processed. One extra EOF byte
probe must be empty. Python hashlib specifies that successive update calls equal
hashing their concatenation. Thus for a stable complete file, streaming and full
read compute the same digest. Both compare to the same stored digest and size,
so their validity decisions coincide. A mismatch triggers the unchanged sink's
fresh exclusive-create publication; a collision refuses without overwrite.

The reusable data buffer has length min(B,N); the loop retains no earlier data
chunks. Hash state, file handle and counters have separate small bookkeeping
costs; tracemalloc tests their actual Python allocation envelope. This does not
bound the existing Frame or encoder. Time and memory improvements are empirical,
not consequences of this equivalence proof.

Unit check: r and d are bytes, so r-d is bytes; B and N are comparable byte
counts. t_e-t_s is a duration in ns and dividing by1000000 gives ms. W ratios and
P ratios are dimensionless. File counts are not physical I/O, tokens or seconds.
Example: N=307200 bytes and B=65536 entails four full chunks and45056 remaining
bytes, followed by an empty EOF probe; zero prefix bytes may be omitted.

Primary API context: Python3.13 hashlib documentation (repeated update semantics)
and tracemalloc documentation (Python allocation scope). This is known API
behavior, not authority-based proof or a novelty claim.

## U / roadmap

Five timing repetitions are descriptive medians/ranges, not calibrated tail
latency, independent task samples or population reliability. CPU frequency,
cgroup sharing, filesystem cache and host scheduling are uncontrolled. No
calibrated combined standard uncertainty u_c or coverage factor k is invented.

Roadmap: pinned-source/ownership check -> excluded construction -> local source
freeze with public-delivery limitation -> seven synchronous first-outcome batches
-> independent raw audit/corruption checks -> bounded candidate/report/evidence
handoff -> additive GitHub PR and exact-main checks when a write-capable route is
available -> only owned dependency-safe branch cleanup. No broad Issue or global
ROADMAP is closed by this study. Do not rerun consumed cases for publication.
