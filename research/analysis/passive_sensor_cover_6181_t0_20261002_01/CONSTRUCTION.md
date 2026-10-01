# Construction receipt — Issue #6184

Formal candidate/auditor runs after construction: **1 / 1**, each one-shot and separately recorded in results/RUN.json. Construction attempts below remain pre-formal receipts.

| Attempt | Outcome | Detail |
|---|---|---|
| 01 | `FAIL_TEST_HARNESS_ONLY` | 6/7 tests passed; `py_compile` passed. The failed assertion expected one feasible cover, but exhaustive enumeration found four feasible supersets and one unique minimum-cost tie. Candidate=0; auditor=0. |
| 02 | `PASS_CONSTRUCTION` | 7/7 tests passed; `py_compile` passed against frozen main 69a1bf509eb432e5e3c0c294d05ad7671d86adb6. Candidate=0; auditor=0. |

The correction changed only the assertion/reporting distinction between `cover_count=4` and `minimum_tie_count=1`. The formal H/T/D/C/U and cost threshold were not changed. Attempt 01 is retained, not relabeled as a scientific failure or silently erased.

Source and fixture identities are in [FREEZE.json](FREEZE.json). The one-shot formal window is 2026-10-01T18:37:00Z–2026-10-01T18:52:00Z; no formal work occurs outside a fresh start-gate check.


## Attempt 03 — refreshed-source construction gate

After updating the pinned main SHA and candidate/auditor constants to `8d6ad7be277fff929a665e4fed44f8ee89b33bad`, the exact frozen blobs were re-read and materialized without byte changes (all five Git blob IDs matched FREEZE.json). `python -B -m unittest test_t0 -v`: 7/7 passed; AST parse: PASS. Candidate formal invocations=0; auditor=0. This is construction only.


## Formal outcome

Candidate and independent CPU-only raw auditor each ran exactly once on 2026-10-01 18:44 UTC; both exited 0. Disposition: `PASS_METHOD_SCOPED`; audit errors=0; retries=0. See [the result and raw artifacts](results/RESULT.md).
