# A02 consumer/classifier composition repair

This is an ordinary source-repair composition staged for the existing PR
#7688 branch. It does not rerun a producer or formal experiment, authorize
a live allocation, or qualify the current-main composition for merging.

## Exact lineage and minimal change

- A02 consumer basis: PR #7688 head
  `df610da674d119b30043b1ae3f78a408621eb409`.
- Corrected classifier basis: PR #7664 head
  `5032d13e2d696fc6c66aa16e2086b0ba751ef70b`.
- Exact corrected classifier Git blob:
  `6a369bc0558684d9d8d141e48325cc14f7531bf3` at
  `missed_admission_guard_v1/candidate_v2.py`.

At the A02 basis, `file_join.py` imported historical `candidate.py` despite
the corrected upstream entry point. Its bundle validator can correctly
reconcile a sample at first input with one missed period and a matching
scheduler summary, then the historical classifier skips that admission-time
row before checking the missed flag. A later kill or map exit is accepted.

The production change is one import: both `classify_run_dir` and the legacy
two-path helper now select `missed_admission_guard_v1.candidate_v2`.
The corrected classifier is copied byte-for-byte from the exact upstream
head; A02 source/event validation and the upstream corrected classifier
implementation are unchanged.
The upstream additive package must be composed before applying this routing
patch. Merely updating the stack base without changing the import is not a fix.

For complete run bundles, from the repository root:

```sh
python research/doom/scorer_eventlog_join_t0_v1/file_join.py \
  --run-dir /path/to/run --research-root /path/to/checkout/research \
  --intent-id recover-1 --max-gap-ns 100
```

## Bounded ordinary verification

The new ten-method suite constructs inert complete bundles in temporary
directories. Accepted intent is at 100, first input at 120, baseline at 110,
and later gain at 130. The 120 row has one missed period. The fixtures first
pass the complete bundle validator, including a scheduler summary with that
missed period, so the policy rejection cannot be attributed to malformed
sidecars. Kill and map-exit event rows are explicitly specified in the tests.

Before the import change, four assertions fail: complete kill bundle,
complete map-exit bundle, actual directory CLI, and two-path helper. All
incorrectly return `ADMISSION_BRACKETED_PROGRESS`. After the import change,
all ten methods pass normally and under optimized Python; both paths reject
with `POST_CANCELLATION_COOCCURRENCE / missed_scorer_period` and
`causal_attribution=false`.

Additional tests preserve a zero-missed admission followed by a later kill
or exit, rejection of admission-only progress, the unchanged gap bound, and
the original interval scope for misses at the chosen baseline or after the
first bounded positive observation.

Verification commands, from the repository root:

```sh
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1 -p 'test_*.py' -v
python -O -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1 -p test_file_join_admission_guard.py -v
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/missed_admission_guard_v1 -p 'test_*.py' -v
python -O -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/missed_admission_guard_v1 -p test_boundary.py -v
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/saved_record_audit_v2 -p test_audit.py -v
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/runtime_bundle_a01_20261005 -p test_candidate.py -v
```

Results: 33 package methods, 10 optimized new-boundary methods, 34 corrected
upstream methods, 18 optimized upstream-boundary methods, 17 saved-audit
methods, and 9 separately run upstream metadata methods pass. These suites
overlap and are not pooled as independent evidence. This is not a full
repository test run. Only ordinary inert unit checks were executed.

## Preserved evidence and limits

A01 remains **HOLD_INVALID_FREEZE**. Its disposition, historical manifest,
raw, freeze and report are unchanged. A02's original ten-row raw, freeze,
report, runners and saved audit results are unchanged; no candidate runner
or producer was repeated. The A02 current manifest and corrected-package
current manifest describe this composition's changed code/documentation.
The original manifest bytes remain available in the exact source commits.

The retained A02 PASS is scoped to its original tested construction cases.
The new boundary claim rests on the new ordinary tests, not a reinterpretation
of historical raw. Correctly reconciling event semantics and selecting the
corrected classifier still cannot authenticate a bundle if all JSONLs and
sidecars are rewritten together. A producer-side immutable manifest binding
JSONL bytes remains required before a live result is called authoritative.

No game, model, OS input, GUI, GPU, container or live/formal allocation ran.
There is no new claim about live cadence, task-effect timing, causality,
recovery efficacy or MAP01 completion. The historical container STOP and
separate live-allocation hold remain.
