# #6501 retained-raw type integrity repair

The retained auditor accepts 150 separate JSON type corruptions of the T0b
raw output: 135 integer-to-float substitutions and 15 zero/one-to-boolean
substitutions. The unchanged raw also passes. The cause is Python equality:
equal-valued integers, floats and booleans compare equal inside dictionaries.

The separate `auditor_v2.py` uses recursive type-sensitive comparison before
accepting replay equality. All 150 variants are rejected, with unchanged raw
still passing. Five regression tests pass. `matrix-audit.json` independently
reconstructs the mutation denominator and each variant digest without importing
either auditor or the scheduler; all five copied-matrix corruptions are rejected.
This matrix audit checks the reported outcomes and reconstruction, not an
independent implementation of the scheduler or a non-author content review.

## Inputs and execution

- Base main: `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.
- Source: `../scope_typed_singleflight_6501_t0b_20261002/auditor.py`.
- Retained raw: predecessor `run01/candidate-raw.json`, SHA-256
  `777df5233313c182850dfe59c65548c5b6db9ac4014006d68db9ee8ee5e1b50b`.
- Fixture SHA-256:
  `42e5c55935497854fdc9eac0ef97cc6569bcbaa9455e88375d030cb7541dfbdf`.
- CPython 3.11.9, Windows 10.0.26300, stdlib-only host process. No timing
  performance claim or resource enforcement claim is made.
- Matrix start/end UTC timestamps and OS identity are in `matrix.json`.

Executed in this directory:

1. `python -m unittest test_types -v` before the repair: 150 failing
   subtests; unchanged control passed (`red-tests-exact-blobs.txt`).
2. The same command after the repair: 5 tests passed (`green-tests.txt`).
3. `python characterize.py`: 150 legacy acceptances, 150 strict rejections.
4. `python check_matrix.py`: `PASS_FINITE_TYPE_MATRIX`, 150/150 rows,
   zero errors, five negative controls rejected.

The initial checkout-based check failed the unchanged control because Windows
Git newline conversion changed fixture bytes. That first construction record
is retained in `red-tests.txt`; it is not type-corruption evidence. Source,
fixture and raw copies were then exported with binary `git show HEAD:path`,
and exact byte identities were used throughout the reported matrix. The first
shared-clone attempt failed on an unavailable promisor object; a separate shallow
sparse HTTPS clone succeeded. Neither setup failure is a scientific outcome.

## Decision and scope

Adopt this supplemental strict comparison for future audits requiring exact
JSON scalar types. Keep the original source, raw and historical T0/T0b verdicts
unchanged. This is a bounded integrity repair and read-only audit of existing
evidence, not a scheduler candidate rerun or new formal allocation. Runtime,
WSLc, Docker, GUI, display, GPU and model invocation counts are zero.

The result covers the 150 specified single-leaf changes in retained raw only.
It does not prove arbitrary malformed-input handling, duplicate JSON member
rejection, real scheduler safety, exactly-once effects, performance or task
benefit. Non-author FINAL-v5 consensus and conditional main application remain
outstanding. The full computer-control goal remains open.
