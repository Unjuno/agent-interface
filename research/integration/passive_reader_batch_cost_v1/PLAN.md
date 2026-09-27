# Issue 3988 — preregistered passive-reader batching cost

Allocation: reader-batch-cost-3988-20260922-01.
Source base: b2457b746a6df06f6536585dfe2ab937aff639f4.
Upstream reader Git blob: ea72c166c2cea511ea91031dfbb14563fe4e3245.
Parent #3876, merged reader PR #3883. Historical #742 is ordering evidence,
not a performance claim. Preserve #3935 and all parallel studies.

## H / T / D / C / U

H1: preserving the exact reader, max_records changes the number of full-file
scans and repeated prefix hashes when draining an already-available backlog.
H2: batch128 median drain CPU is <=0.50 of batch1 at N2048, equal correctness.
First returned batch latency is a separate descriptive metric, not a gain gate.

T: static N128/N512/N2048, exact 256-byte LF-terminated records; batches1/32/128;
three repetitions in Latin order (1,32,128), (32,128,1), (128,1,32) within each N.
All 27 children are fresh exec processes pinned to guest CPU0. Warm the file
before timing. Keep max_bytes=1048576 and all prefix checks. A measured drain
is followed by one untimed accounting drain that delegates to the same file and
SHA implementations; its clocks are diagnostic and are never pooled with timed
samples. A separate final empty-tail read is outside both drains. Timing spans
read calls, list/trace bookkeeping and clock calls, not imports, startup,
serialization or output writes. It is not an isolated hash microbenchmark.
Retain every returned event byte and per-call count/offset/sequence/tail/flags,
terminal cursor and all subprocess stdout/stderr/exit receipts. Content-addressed
identical objects are lossless deduplication, not replacement by summary hashes.
Each child has a 10-second supervisor limit. One outer run uses a 40-second tool
envelope; preserve STOP/partial artifacts if it cannot finish. No retry/tuning.
Construction uses N16/N64 and four cells, separate from the formal denominator.

D: complete27, exact bytes/order/cursors/tails, neutral authority and exact
accounting must pass the separate raw auditor and ten corruption controls.
Then median timed CPU ratio128/1 at N2048 <=0.50 gives
PASS_READER_BATCH_COST_SCOPED. Complete valid evidence with ratio >0.50 gives
HOLD_BATCH_CPU_BENEFIT_NOT_ESTABLISHED. Integrity/semantic disagreement is FAIL;
missing source/environment/exit/timeout evidence is STOP/HOLD. Report all three
raw repetitions and medians/ranges; never censor a slow row.

C: loop bookkeeping, allocations, cache behavior and OS scheduling accompany
prefix hashing, so this does not identify a unique bottleneck. Larger batches
may delay first return. All events exist already; no wait-to-fill policy,
producer concurrency, model consumer, CLI startup or retention transaction is
measured. Buffered read bytes are not disk traffic. Do not skip prefix checks,
change shared defaults, or infer model/task/production gains.

U: supplied Linux/x86_64 execution container, CPython3.13.5, no Docker CLI or
image identity. Guest CPU0 affinity is not physical-core isolation. Frequency is
not locked; snapshot MHz and clocks are retained, not treated as fixed frequency.
Three repeated deterministic inputs quantify observed variation only, not a
population confidence interval or stable p95. No host GUI, model, provider,
network experiment, install, ACK or input. Audit is separately written code and
process by the same assistant, not external human replication.

## Analytical accounting and variable table

| Symbol | Meaning | SI/unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| N | Number of retained records | 1 (count) | Corpus length in records | 128,512,2048 | integer scalar |
| B | Record limit per call | 1 (count) | max_records | 1,32,128; divides N | integer scalar |
| L | Serialized record length | 1 (byte count) | 256 bytes including LF | fixed positive | integer scalar |
| S | File length | 1 (byte count) | N L | <=1048576 bytes | integer scalar |
| m | Drain calls | 1 (count) | N/B | stops at first end | integer scalar |
| j | Call index | 1 (count) | 1 through m | integer | integer scalar |
| R | Bytes returned by read | 1 (byte count) | S m | accounting pass only | integer scalar |
| H | SHA input bytes | 1 (byte count) | sum of old/new prefix lengths | accounting pass only | integer scalar |

Bytes are dimensionless information/storage counts, not SI physical lengths.
Each call starts at file offset0 and reads the complete S-byte file. Therefore
R = sum(j=1..m) S = S m. Before call j the consumed prefix has length (j-1)BL;
after it has length jBL. H = sum(j=1..m) ((j-1)BL+jBL)
= BL sum(j=1..m)(2j-1) = BL m^2 = S m. There are m opens/reads and 2m SHA calls.
The sum identity follows from 2[m(m+1)/2]-m=m^2. Counts times bytes produce bytes
in both equations. No final empty check is included. For N2048/B128/L256,
S=524288, m=16, R=H=8388608 bytes; for B1, R=H=1073741824 bytes.
This is exact accounting for this source/fixture, not a latency proof.

## Bounded roadmap

Intake/source reconstruction -> excluded construction/tests -> public hash freeze
-> one formal27-case run -> separate raw audit/controls -> additive PR with all
raw/source and readback -> merge only with justified integration gates -> own
branch cleanup only after dependency check. Global ROADMAP/#3876/#57 remain open.
