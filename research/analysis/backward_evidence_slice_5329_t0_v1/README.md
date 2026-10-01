# Issue #5329 — backward evidence slice T0

This package tests the unverified backward-slice construction idea recorded in
Issue #5329 comment #5923874105. It is separate from the earlier four-packet
task-conditioned bottleneck toy, Blackwell/deadline addendum, and production
full/summary caller measurement.

Formal allocation: `5329-backward-slice-t0-20261001-01`.

## H / T / D / C / U

- **H:** On a finite event/dependency graph, a backward slice retaining data,
  control, freshness/invalidation and explicit unknown-cause dependencies can
  preserve one declared evidence decision while excluding irrelevant trace
  noise. Data-only or label-only summaries should miss a stale/control
  counterexample; incomplete graphs must yield `UNKNOWN`.
- **T:** Four deterministic cases: clean trace plus 12 irrelevant events, stale
  generation, skipped verifier/control branch, unresolved external cause.
  Compare `RAW_TRACE`, `LABEL_ONLY`, `DATA_SLICE`, and `TYPED_SLICE`; independently
  replay closure and the declared oracle; apply four integrity mutations.
- **D:** `PASS_METHOD_SCOPED` only if raw and typed slice match the oracle in all
  rows, clean typed slice is strictly smaller, data-only misses both stale and
  skipped-verifier controls, unresolved external cause yields `UNKNOWN`, and all
  four mutations are rejected. Any unverified gate is STOP, not PASS.
- **C:** The finite graph/truth table is authored; fixed lossless fields may be
  simpler; slice construction cost may erase its compression gain.
- **U:** No test of real dependency completeness, GUI causality, empirical token,
  bandwidth, latency or production benefit.

## Result

`STOP_PROVENANCE_OR_RUNNER`. The runner completed once and emitted four rows;
the frozen auditor then exited 1 with `KeyError: 'external_cause'` on the
deliberately unresolved dependency edge. This is an auditor construction STOP,
not a scientific PASS/FAIL. Raw and exact traceback are retained. Do not rerun
or patch this allocation; a corrected attempt requires a separately frozen
successor and output path.

See `FREEZE.md`, `SOURCE_MANIFEST.json`, and `results/formal01/`.
