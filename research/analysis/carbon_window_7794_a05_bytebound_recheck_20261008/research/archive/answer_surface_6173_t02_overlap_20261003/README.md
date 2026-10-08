# Issue #6173 T0-02 denied-attempt packet — overlap-preserved

## Disposition

This archive preserves the complete 16-file package from branch
`research/answer-surface-6173-denied-attempt-02-20261002` at immutable tip
`b975d94ab13afab14a2f3a52900aac828ca300e3`. The owner explicitly recorded
that T0-02 overlapped the concurrent T0b denial-boundary result and would not
receive a separate research PR; its files were retained on this branch for
audit/recovery. The later factorized-axis successor T0-03 was integrated in
PR #6185 and is a separate 17-case allocation.

The original T0-02 report records `PASS_METHOD_SCOPED` for its frozen 13-case
synthetic fixture, with one candidate and one raw-only auditor invocation and
no retries. This archive does not assert novelty: the owner disclosed overlap
with T0b, and T0-03 later evaluated a distinct factorized representation.
T0-02's output, source, freeze, raw inputs, tests, and reports remain verbatim
and are not pooled, rescored, or replaced by either neighboring result.

This is synthetic method evidence only. It is not a real benchmark
contamination finding or proof of production monitoring completeness. No
candidate, auditor, or construction test was run during this rescue; the
consumed allocation was not replayed.

## Exact-byte preservation

`MANIFEST.json` records the immutable source tree and all 16 original Git blob
IDs, byte sizes, and SHA-256 values. `VERIFICATION.json` records static
file-by-file identity checks. The package is stored below `research/archive/`
so the result is preserved without presenting a duplicate as a current
research-index result.
