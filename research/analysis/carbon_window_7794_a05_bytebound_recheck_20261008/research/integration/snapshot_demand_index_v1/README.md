# Demand-built prefix index — Issue #4068

## Result and narrow decision

**PASS_DEMAND_INDEX_CONTRACT_SCOPED** and **PASS_DEMAND_INDEX_FIRST_RETURN_SCOPED**.
One publicly hash-frozen allocation completed 18 timing cases and 30 contract cases.
All 19 worker exits and two external batch-child exits are observed 0. No retry,
replacement, pooling or post-freeze source change. The separately implemented raw
checker reports zero errors and rejects 10/10 copied-evidence corruptions. This is
same-author checking in a separate process, not independent human review.

This reduces the first-return regression of the prior **eager immutable snapshot**.
It does **not** replace the live reader or improve every endpoint: the original
file reader still returns the first page faster. No runtime or default is changed.

## H / T / D / C / U

| Item | Frozen question and boundary |
| --- | --- |
| H | Demand-built prefix checkpoints preserve eager query semantics; at 4,096 records/page32, eager/lazy first-return median ratio is at least 1.5 and lazy/eager full-drain ratio is at most 1.20. |
| T | 1,024 and 4,096 records, 256 UTF-8 bytes per line, original/eager/lazy, three Latin-rotated repeats: 18 fresh worker processes in two immutable nine-case batches. One separate worker evaluates 10 contract fixtures across all three policies: 30 cases. |
| D | Complete source/input/response/cursor/process/clock accounting plus raw-only audit and corruption controls is required for contract PASS. Timing gates are independent; no favourable subset or silent retry. |
| C | Lazy private memo is single-owner. Increasing boundaries extend one hash state; uncached backwards queries recompute from zero. Full snapshot SHA still costs linear work before first return. |
| U | Three repeats and one guest environment; no population tails, calibrated uncertainty, live producer, shared-cache concurrency, model/GUI/ACK/input authority, disk-throughput or product claim. |

The complete preformal PLAN.md, including the variable table, finite reasoning,
dimensional checks and exact schedule, is retained inside the archive. No equation
or empirical claim relies on a lost notebook.

## Measured result

Milliseconds, median [minimum, maximum], three fresh processes per cell;
page32 is already the original default. Timed endpoints include actual snapshot
capture/preparation, response retention and final empty check; imports/startup,
file generation, cache priming and JSON output are outside the interval.

| Records | Policy | First returned page (ms) | Complete drain (ms) |
| ---: | --- | ---: | ---: |
| 1,024 | ORIGINAL | 0.356237 [0.347109, 0.385100] | 19.537254 [17.829201, 20.338033] |
| 1,024 | EAGER | 1.422603 [1.337006, 1.807364] | 9.554991 [6.859460, 11.680279] |
| 1,024 | LAZY | 0.692210 [0.568385, 0.743273] | 5.699390 [5.444819, 6.286027] |
| 4,096 | ORIGINAL | 0.798609 [0.737472, 0.855463] | 330.100443 [224.397300, 477.470516] |
| 4,096 | EAGER | 5.040070 [4.858362, 8.984877] | 29.244287 [24.270614, 44.060700] |
| 4,096 | LAZY | 1.606770 [1.581304, 3.031871] | 27.588896 [25.798373, 40.281303] |

Main preregistered ratios: eager/lazy first return **3.1367712864940223**;
lazy/eager total **0.9433943799005939**. Both gates pass. However LAZY first return
is still about **2.01 times slower than ORIGINAL**. Wide ranges are retained, not
filtered. The experiment does not identify hash cost separately from allocation,
copying, JSON decoding, loop bookkeeping and guest scheduling.

Environment: supplied Linux 6.18.44 x86_64 execution container, CPython 3.13.5,
OpenSSL 3.5.5, Intel Xeon Platinum 8370C guest description; allowed CPUs0-4,
worker affinity guest CPU0, sampled 2793.438 MHz, frequency not fixed and no
physical-core isolation. Docker/gh absent locally. No Docker/OrbStack pinned-image
or network-none attestation; no external-network experiment, provider/model,
GUI/input, user data, installation or shared-runtime change.

## Semantics and limits

The exact old FrozenSnapshot read/capture/metadata methods are inherited unchanged.
Only preparation changes to a memoized prefix mapping. Every returned prefix digest
and line count is checked against the same immutable bytes. Reverse/repeated reads,
wrong hash/sequence/midline/Boolean/foreign cursors, partial tail, malformed JSON,
duplicate keys and nonfinite constants reconcile with a separate raw oracle.
Iteration of the memo enumerates cached entries, not a public all-boundaries API.

The snapshot is historical, not a fresh file read. It does not follow appends,
certify coherent acquisition, authenticate producer epochs, acknowledge consumption
or authorize input. Avoid composing this component PASS into desktop acceptance.
The possible integration decision is historical-evidence retrieval only.

## Exact provenance and preservation

Intake main: `2308b8301d69b7089a2e0636486736ed59b61537`.
Preformal public hash commitment: `f205e0fab428840fb7728b04e488bf36f45ae207`,
Issue #4068 comment5768715715; first-result comment5768726217.
Full source/raw publication follows execution; it is not claimed to predate it.

- FREEZE SHA256: `abe7c557fce23c814d7093eee844e61b07d428e21b42d19d3a494d53317068e4`.
- Exact upstream reader Git blob: `ea72c166c2cea511ea91031dfbb14563fe4e3245`.
- Eager source SHA256: `b3f4e81be3389b40cccb6b435e1f6bc1ded1bf0697312475a54523d430001232`.
- AUDIT SHA256: `e4d58d83ea997e36fdca96213065b1e2841308520e08b6fc4dd93c6bae19308c`.
- Archive: 36,104 bytes, SHA256 `5ccd8540226a46f3ea29616c8b1171019dd0e8badd5d7a8d7d5d3027544d88d8`.

All 103 original files / 4,933,391 member bytes are losslessly retained in five
parts and ARCHIVE.json. FILES.json covers the other 102 files. It includes exact
inputs, every raw response, source, commands, process/batch receipts, construction,
frozen plan/environment and original audit. The unpacker verifies all before
writing into an absent destination; it executes no experiment. Local restoration
was byte-identical, the unchanged auditor reproduced the original output and five
unit tests passed. Five packaging refusal controls pass; see PUBLICATION_CHECK.json.

Prior #3985/#4012 and the conversation-local 62-case b7e1 result remain unchanged.
Their read-only revalidation was done without rerunning either formal experiment.
The complete old archives remain conversation-hosted and are **not** included or
claimed public here; the exact comparator source needed for this new allocation
is included. A failed optional old UTF-8 repacker encountered a binary member;
that publication diagnostic altered no original bytes or scientific allocation.

## Re-audit only

From this directory, use an absent destination:

```sh
python -B unpack.py /tmp/issue4068-review
python -B /tmp/issue4068-review/audit.py /tmp/issue4068-review
cd /tmp/issue4068-review
python -B -m unittest -v test_contract
```

Do not rerun consumed run.py worker/batch/supervise commands. No Python -O.
No dependency installation is needed for this standard-library raw audit.
Repository-wide CI/review and main delivery are separate recorded gates. This
bounded study does not complete the repository ROADMAP. #3876's administrative
closure is not production acceptance; do not infer a still-open tracker from old
archived wording. Only #4068 is eligible to close after its evidence delivery.
