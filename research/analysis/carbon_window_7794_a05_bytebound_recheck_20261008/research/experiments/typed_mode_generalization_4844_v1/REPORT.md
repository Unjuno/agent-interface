# Issue #4844: typed-mode diagnostic result

**Disposition: `STOP_PROVENANCE_OR_AUDIT`.** The container audit of the emitted JSON passed, but GitHub byte-readback found that the committed frozen source files differ from the exact locally executed files: GitHub's experiment.py/audit.py blobs have a trailing CRLF (`experiment.py` SHA-256 `a10bcd36625e1410b0872b08788b26bf47f34e62ad17e82259c1aa25dbf6def8`, audit.py `eee772fa1d3052dc3f1cabcc9296a218b4f0f07bdca00240f048b2adfda3ec56`) while the executed/frozen files were `31d5cebd2d4cf348780ad6f6b14b86fc8921e115a05ad6c3c5449cdbabaaa6e9` and `593cb9b4fe3d64df22186ca74cae7acc9cec3a52439d48692f71fd5b05b5aef7`. The numerical output below is retained as exploratory raw evidence only; it is not a valid formal result and must not be used to accept/reject the hypothesis. The consumed invocation is not retried.

## H / T / D / C / U

**H.** Mode-factorized inference may preserve multimodal cues for modes sharing a recovery, reducing wrong emitted recoveries under partial observation; coverage may regress.

**T.** The exact protocol, branch, source hashes, seeds and thresholds were frozen in [PREREGISTRATION.md](PREREGISTRATION.md) before the one heldout invocation. Standard-library Bernoulli Naive Bayes, alpha 1, six binary cues, five modes, map `[0,0,1,2,2]`, 2,000 balanced training rows and 3,000 heldout rows across four frozen blocks. Container: `python:3.11-bookworm`, image `sha256:e635facd4cd70a0e0b5d72cb0ce38f24434b6e98e11c2383d428a880c0f7232c`, Docker 29.8.0, Linux/amd64, network disabled, read-only root/source, 1 CPU, 512 MiB, 32 PIDs. One formal run; no retry or GPU reservation.

**D.** Per-block wrong emitted dispositions / safe coverage:

| Heldout block | Direct wrong / coverage | Typed wrong / coverage | Outcome |
|---|---:|---:|---|
| Cue 1 missing | 32 / 28.13% | 59 / 76.13% | Typed has more wrong emissions |
| Cue 4 missing | 59 / 64.53% | 49 / 79.47% | 16.95% fewer errors, below 25% gate |
| Two cues missing | 24 / 26.80% | 64 / 71.33% | Typed has more wrong emissions |
| Contradictory cues | 142 / 68.40% | 86 / 49.87% | 39.44% fewer errors, but coverage −18.53pp |

Exploratory metrics from the retained raw output: the full-observation five-mode control was correct and the arms agreed. Both arms abstained on all-missing unknown and the frozen contradictory control. Independent structural/summary audit passed with zero errors and rejected both corruption controls (2/2). If source identity had passed, no block would meet the frozen conjunction of >=25% fewer wrong emitted dispositions and <=5pp coverage loss; the contradictory block loses 18.53pp coverage. These metrics do not override the terminal provenance STOP.

**C.** Authored prototypes and independent Bernoulli cue assumptions define this toy task. The contradictory control is a construction-selected vector, not a random population. No real GUI/task transfer, statistical generalization, authority/safety proof, latency benefit, or GPU benefit is claimed. Safe dispositions are labels in the synthetic simulator only.

**U.** Whether the tradeoff persists across preregistered seeds, realistic cue dependencies, and independently authored fault families remains unknown. No model/runtime promotion follows. Preserve Issue #4155 and its evidence unchanged.

## Evidence

- `formal01/result.json.gz`: lossless gzip envelope of the complete 3,000-row exploratory result JSON; SHA-256 and byte length recorded in `formal01/MANIFEST.json`.
- `formal01/runner.stdout.txt`, `runner.stderr.txt`, `audit.stdout.txt`, `audit.stderr.txt`: exact local container output (stderr files empty).
- `formal01/MANIFEST.json`: command, source/image identities, raw and log hashes, invocation count, and disposition.
- `audit.py`: independent result-structure and block-summary audit; 2/2 mutation controls rejected.
