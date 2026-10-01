# Construction receipt — Issue #6184

Formal candidate/auditor runs: **0**. This records pre-formal test construction only.

| Attempt | Outcome | Detail |
|---|---|---|
| 01 | `FAIL_TEST_HARNESS_ONLY` | 6/7 tests passed; `py_compile` passed. The failed assertion expected one feasible cover, but exhaustive enumeration found four feasible supersets and one unique minimum-cost tie. Candidate=0; auditor=0. |
| 02 | `PASS_CONSTRUCTION` | 7/7 tests passed; `py_compile` passed against frozen main 69a1bf509eb432e5e3c0c294d05ad7671d86adb6. Candidate=0; auditor=0. |

The correction changed only the assertion/reporting distinction between `cover_count=4` and `minimum_tie_count=1`. The formal H/T/D/C/U and cost threshold were not changed. Attempt 01 is retained, not relabeled as a scientific failure or silently erased.

Source and fixture identities are in [FREEZE.json](FREEZE.json). The one-shot formal window is 2026-10-01T18:45:00Z–2026-10-01T19:00:00Z; no formal work occurs outside a fresh start-gate check.
