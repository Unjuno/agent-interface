# Issue #6689 T0 stop record

Status: `FAIL_AUDIT` — `STOP_CLASSIFICATION_COUNT_CONTRACT`.

The frozen candidate ran once and emitted 4,707 prefix rows across 2,592
interleavings and 40 authored worlds. The independent raw-only auditor ran once
and exited 2. It agreed with all row classifications and rejected all four
mutation controls, but rejected the header's `classification_counts`: that map
contains the extra derived keys `EARLY_STABLE_FAIL` and
`EARLY_STABLE_UNKNOWN`, while the auditor correctly counts only the three
disposition-class labels. This aggregate-contract mismatch invalidates the
audit; no `PASS_METHOD_SCOPED` claim is made.

The exact candidate and auditor were each run once; retries were zero. Per the
freeze, neither source nor output was repaired or rerun. The immutable raw and
audit evidence is in [`results/formal-01/`](results/formal-01/); hashes and
counts are recorded in [`STOP.json`](STOP.json). Any fix must be a separately
frozen successor allocation. The result is limited to a deterministic authored
finite model and says nothing about runtime freshness, real source behavior,
GUI, action authority, product effects, or performance.
