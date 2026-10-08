# Issue #8157 A05 posthoc retained-raw score audit

## H / T / D / C / U

**H.** The immutable A02 raw may already show whether the interval estimator added measurable value under A02's declared score rule, despite A02's formal auditor reconstruction failure. This audit will not repair or replace that formal result.

**T.** One independent audit-only pass over the exact public, oracle, and candidate JSONL artifacts whose SHA-256 values are pinned by A04. Reconstruct all candidate estimates prefix-by-prefix, recompute the calibration-control threshold for point TTC and interval upper bound using calibration controls only, and report the original A02 D-rule components per profile. No generator, candidate, A02 auditor, or A04 auditor is invoked. The A04 report must already say `PASS_RAW_RECONCILIATION_ONLY` and its SHA must match this freeze.

**D.** The sole allowed positive diagnostic is `NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW`: raw reconstruction has no mismatches, in-model interval coverage is at least 50% in each declared in-model profile, no in-model containment misses occur, and the frozen A02 improvement/hazard-yield conditions are not met. Any other pattern is `MIXED_OR_INCOMPLETE_DIAGNOSTIC`. These are posthoc diagnostics only; neither result changes A02's formal `FAIL_METHOD` or constitutes a new method allocation/pass.

**C.** Scoring thresholds and outcome counts depend on the retained A02 sample and candidate output. A05 is a second auditor of that same data, not independent replication or a new sample. Recomputed outputs do not cure the original A02 audit failure.

**U.** Synthetic finite-method evidence only. It does not test or authorize real-time control, real scenes, GUI/game behavior, or any live allocation.

## Freeze and one-shot execution

- A02 formal disposition remains `FAIL_METHOD`; A03 remains its preserved stop; A04 remains a raw-reconciliation-only pass.
- Inputs are accepted only when their byte hashes match `FREEZE_A04.json`; A04's report hash is also recorded in the output.
- Run once in the already cached WSLc pinned Python image with network disabled, one CPU, 512 MiB, read-only source/input and a dedicated writable output directory.
- Run the A05 audit program exactly once. Any nonzero exit, mismatch, or interruption is retained as-is; no retry, tuning, or replacement run.
- No candidate or generator invocation occurs in A05. This is not a formal repeat of A02/A04.
