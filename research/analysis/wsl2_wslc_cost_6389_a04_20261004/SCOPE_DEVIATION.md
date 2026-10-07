# A04 result and preregistration scope deviation

Formal candidates completed exactly once: three native/WSLc pairs, six
invocations total, zero retries. The independent raw-only auditor reports
`PASS_PORTABILITY_ONLY`.

## Outcome

| Arm | Pair 1 (s) | Pair 2 (s) | Pair 3 (s) | Median (s) |
|---|---:|---:|---:|---:|
| Native Ubuntu/WSL2 | 125.073363 | 132.668937 | 190.521730 | 132.668937 |
| WSLc | 123.623223 | 123.301019 | 199.073337 | 123.623223 |

Every one of the six invocations passed both suites: **445 protocol tests and
205 harness tests (650 total)**. All result runner hashes were identical to
the frozen runner; all raw log hashes matched `result.json`; the independent
auditor found matching counts and PASS across all pairs. The native median was
7.32% slower than WSLc, so the preregistered 10% native improvement threshold
was not met. This is portability evidence for this exact suite, not an
iteration-cost win.

## Disclosed deviation

`README.md`/`FREEZE.json` initially described the A04 workload as a 205-test
suite by carrying forward the earlier A08 report's count. The exact A04 source
was frozen at main `8094af4631fc7bc5d92990e5151d5e89477ee39f`; its pinned
`runtime/integration_checks/native.py` actually ran 445 protocol plus 205
harness tests. The runner/source hashes were fixed before execution, the same
complete runner was used in both arms and no tests were removed or substituted.
Therefore the empirical comparison is about the 650-test suite at frozen main,
not the earlier 205-test suite. A08 timings were not reused. The stale count
description is retained in the preregistration history; this file qualifies
the scope and does not retroactively rewrite it.

WSLc emitted the cgroup/swap-limit warning on all launches. `--memory 512M`
was requested but is not claimed as enforced. No Docker comparison, peak-RSS,
OOM-prevention, GUI/model, hosted-Actions, or repository-wide migration claim
follows. The first construction preflight's incomplete wrapper receipt is
preserved in `PRECHECK-01.md`; the corrected preflight passed in
`PRECHECK-02.json`.
