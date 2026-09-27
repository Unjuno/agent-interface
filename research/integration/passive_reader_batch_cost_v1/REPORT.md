# Issue 3988 — passive-reader backlog batching cost

**Decision: PASS_READER_BATCH_COST_SCOPED.** One frozen allocation, 27 fresh
child processes, zero retries. This is experimental-reader backlog cost evidence,
not production integration, model receipt, useful task feedback or token savings.
Parent #3876 and the repository roadmap remain open. No shared implementation,
prefix check, default setting, historical result or other agent branch is changed.

## Finding

On 2,048 already available records, raising the per-call limit from 1 to 128
reduced median measured drain CPU from 1,479.344 ms to 19.309 ms. The ratio is
0.013052068233181342, below the preregistered 0.50 gate. The existing default
limit 32 took 53.612 ms. However, first-return median rose from 0.359 ms at
limit 1 to 1.025 ms at limit 128. Backlog throughput and first-notification
responsiveness are different endpoints; this result does not justify blindly
changing the default or waiting to fill a batch.

Both the timed and separately instrumented paths returned the complete exact
payload in sequence in every cell. Final cursors, empty-tail behavior and
neutral authority flags all reconciled. File-read and SHA-input byte counts
matched the frozen analytical prediction exactly: at 2,048 records, each was
1,073,741,824 bytes for limit 1, 33,554,432 for limit 32 and 8,388,608 for limit
128. These are bytes supplied by buffered reads/to SHA, not physical disk I/O.

## H / T / D / C / U

H: batching the already available backlog should reduce repeated complete-file
scanning and old/new consumed-prefix hashing without changing payload/cursor
semantics. The empirical gate is at least a twofold median drain-CPU improvement
for limit 128 versus 1 at 2,048 records. First-return latency is descriptive.

T: the exact main reader is unchanged, Git blob
`ea72c166c2cea511ea91031dfbb14563fe4e3245`, source base
`b2457b746a6df06f6536585dfe2ab937aff639f4`. Three lengths (128, 512, 2,048),
three limits (1, 32, 128), three Latin-ordered repetitions: 27 fresh processes.
Each static line has 256 bytes including LF; max_bytes remains 1,048,576.
The file is warmed before timing. Each child performs one timed drain, one
separately labelled untimed delegated accounting drain, then an empty-tail
control outside both. There is no live producer, model, GUI or input.

D: exact denominator/order/payload/cursor/neutral flags, byte accounting,
source hashes, child exits and raw audit must pass before interpreting the CPU
gate. All passed. A missed CPU gate would have been HOLD; no row was discarded,
replaced or retuned. Formal orchestration exit 0 was independently retained in
EXECUTION.json, with 11.399388833 seconds of outer wall time. Each child had a
10-second timeout; none fired. Eight excluded construction tests and ten
semantic corruption controls passed; construction is not pooled with formal.

C: CPU savings include Python calls, allocations and minimal host list/trace
bookkeeping, not only hashing. Larger batches can delay the first return.
Static, complete logs do not test wait-to-fill, producer scheduling, persistence,
concurrent readers, incomplete tails or end-to-end usefulness. Prefix guards
were not weakened to obtain the result.

U: three repetitions quantify the observed range, not a population confidence
interval or a stable tail estimate. OS scheduling, cache effects and unlocked
CPU frequency remain uncertainty sources. No combined calibrated uncertainty
or coverage factor is assigned. This does not establish Docker/OrbStack parity,
physical disk traffic, ACK, exactly-once handling, GUI/task success or product
performance. Independent audit means separate code/process by the same
assistant, not external human review or second-machine replication.

## Measurement conditions and complete summary

Supplied Linux 6.18.44 x86_64 execution container; CPython 3.13.5, glibc 2.41;
guest AMD EPYC 9V74, 2,596.126 MHz snapshot (not a locked frequency). Five guest
CPUs visible; children pinned to guest CPU 0. Cgroup CPU quota 4 CPU equivalents,
memory 4 GiB; physical-core exclusivity not established. Docker CLI and immutable
image identity unavailable. No package installation or experimental network use.

CLOCK_PROCESS_CPUTIME_ID measures the timed process CPU; CLOCK_MONOTONIC measures
elapsed/first-return intervals. Both report 1 ns resolution, not 1 ns accuracy.
Imports, startup, serialization and output writes are excluded; read calls,
clock calls and minimal per-call host bookkeeping are included. Values below are
median [minimum, maximum] in milliseconds over three fresh processes per cell.
Accounting counters are identical across the three repetitions.

| Records | Batch | Drain CPU ms | Drain wall ms | First return ms | Read bytes / SHA bytes, each |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 1 | 11.132 [10.992, 13.438] | 11.128 [10.990, 13.432] | 0.290 [0.157, 0.600] | 4,194,304 |
| 128 | 32 | 1.391 [1.223, 1.432] | 1.389 [1.220, 1.428] | 0.338 [0.317, 0.464] | 131,072 |
| 128 | 128 | 1.352 [0.858, 1.414] | 1.349 [0.854, 1.412] | 1.346 [0.851, 1.409] | 32,768 |
| 512 | 1 | 103.915 [103.614, 132.559] | 103.906 [103.765, 132.913] | 0.359 [0.252, 0.385] | 67,108,864 |
| 512 | 32 | 5.720 [5.618, 6.185] | 5.717 [5.614, 6.180] | 0.507 [0.408, 0.555] | 2,097,152 |
| 512 | 128 | 3.471 [3.031, 4.066] | 3.468 [3.027, 4.063] | 1.170 [0.952, 1.220] | 524,288 |
| 2048 | 1 | 1479.344 [1463.022, 1518.557] | 1480.190 [1463.446, 1519.119] | 0.359 [0.352, 0.501] | 1,073,741,824 |
| 2048 | 32 | 53.612 [53.458, 55.271] | 53.606 [53.588, 55.529] | 0.534 [0.449, 0.588] | 33,554,432 |
| 2048 | 128 | 19.309 [19.119, 19.753] | 19.335 [19.115, 19.749] | 1.025 [0.930, 1.102] | 8,388,608 |

## Exact accounting

The full derivation, variable domains, units and dimensional check are frozen in
[PLAN.md](PLAN.md). At fixed corpus size, the reader opens at zero and rereads the
whole file on every drain call; it hashes both the old and new consumed prefixes.
The prefix-length arithmetic predicts the exact observed bytes. It does not
predict the measured speedup: timing remains an empirical result.

## Evidence and preservation

Preformal hash registration: Issue #3988 comment 5766579835. First outcome:
comment 5766593998. Allocation `reader-batch-cost-3988-20260922-01`.

- FREEZE.json SHA-256: `b0731bb81d79c1af2453c2e2d54a94297147a906c517a98f6ef513f1797ac960`.
- formal-01/RAW.json: `a269de5939150d8673f9fd14b06c645f54d069f6b552e5130411334af4b10ae3`.
- AUDIT.json: `94b5e7eaeb7894cde881db4e28066e22ffc0052cf1cc3a5708073bfb9070fad8`.
- Evidence archive: 28,220 bytes, SHA-256 `b2cb261b59cf9423603bead9c185f488f126e77154176de13b0337f11753a7d7`.

BUNDLE.json names four base64 transport parts of a deterministic tar.xz archive.
They retain all 106 original files (1,671,611 expanded file bytes): exact source,
input corpora, environment, freeze, four excluded construction cases, all 27
formal stdout/stderr/process receipts, every returned payload and per-call trace,
content-addressed objects, raw audit and first-outcome logs. Deduplication is
lossless; source/data are not replaced by unrecoverable digest-only summaries.
Readable runner, auditor, tests, reader, plan and freeze are also provided beside
the archive and must match their extracted counterparts.

The remote Git object IDs of the readable runner/auditor and all four parts were
checked against local bytes before PR creation. A fresh local extraction
reconstructed all files; the frozen auditor reproduced AUDIT.json byte-for-byte
and all 8 construction-auditor tests passed. No new benchmark was run during
that package check. PACKAGE_CHECK.json records this extra delivery verification;
it is postformal and does not change the frozen auditor or original result.

The old #3935 source-publication STOP and docs-only PR #3962 remain untouched.
This stdlib backlog study is a different experiment, not a retry or alternative
publication of that blocked source. Parallel crash/epoch/rotation/partial-tail
allocations remain separate; this study holds the source fixed.

## Re-audit without rerunning the experiment

From this directory, select a new output directory. Python 3.13 standard library
is sufficient; the offline audit does not require guest CPU affinity or a GUI.
The unpack command verifies exact hashes, member counts, sizes, regular paths
and a fresh destination. It does not execute the runner.

```sh
python -S -B unpack.py /tmp/reader-batch-3988-evidence
python -S -B /tmp/reader-batch-3988-evidence/audit.py \
  /tmp/reader-batch-3988-evidence/formal-01 > /tmp/reader-batch-3988-audit.json
cmp /tmp/reader-batch-3988-audit.json /tmp/reader-batch-3988-evidence/AUDIT.json
python -S -B -m unittest discover -s /tmp/reader-batch-3988-evidence \
  -p test_audit.py -v
```

Do not rerun the consumed formal allocation. A new performance measurement needs
its own environment/affinity preflight, fresh allocation and source/input freeze.
The frozen runner has no `FORMAL_CONSUMED` enforcement; that external marker and
no-retry policy are provenance controls, not a general replay-prevention feature.

## Integration handoff and bounded roadmap

Completed: intake/source identity, excluded construction, preformal public hash
freeze, one formal allocation, independent raw reconstruction and corruption
controls, complete source/raw packaging and local extraction verification.
PR review/checks, main readback and safe own-branch cleanup are publication gates,
not new scientific experiments; use the PR's live state for those dispositions.

Systems application: reduce redundant reads while keeping prefix validation.
Queueing application: separate already-present backlog drain from wait-to-fill.
Human-computer interaction application: distinguish first evidence delivery from
bulk completion; no human-tempo result is measured here. The next useful test is
a separately frozen live producer workload with a backlog-aware limit and a
first-response budget, not unconditional limit 128 or a new generic queue.

## ERROR CHECK

Formal 27/27, one invocation, no retry; accounting pass not pooled with timing;
10/10 rehashed corruption controls rejected; source/freeze/raw hashes preserved;
first-return regression retained; no ACK/action authority or broad promotion.
The parent process receipt was checked separately because frozen audit.py checks
child exits but does not itself read EXECUTION.json.

Clock definitions: [official Python time documentation](https://docs.python.org/3.13/library/time.html).
Buffered-stream distinction: [official Python I/O documentation](https://docs.python.org/3.13/library/io.html).
