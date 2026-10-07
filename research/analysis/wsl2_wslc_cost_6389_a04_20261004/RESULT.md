# A04 representative suite result — #6389

**Independent disposition: `PASS_PORTABILITY_ONLY`**, with the preregistration
suite-count discrepancy disclosed in [`SCOPE_DEVIATION.md`](SCOPE_DEVIATION.md).

| Runtime | Pair 1 (s) | Pair 2 (s) | Pair 3 (s) | Median (s) |
|---|---:|---:|---:|---:|
| Native Ubuntu/WSL2 | 125.073 | 132.669 | 190.522 | 132.669 |
| WSLc | 123.623 | 123.301 | 199.073 | 123.623 |

All 6 candidates exited 0 and ran the same frozen runner hash. All 6 passed
445 protocol plus 205 harness tests (650 total), with equal counts in every
arm/repetition. The raw-only auditor verified the `result.json` log hashes and
matching outcomes. Native was 7.32% slower at the median; it did not meet the
preregistered 10% improvement threshold. This supports compatibility for the
frozen contract suite, not a native cost advantage.

Three WSLc preflights verified idle state and the exact local image ID. The
runtime emitted the cgroup/swap warning each time; `--memory 512M` is only a
request. No enforced memory cap, OOM reduction, Docker comparison, GUI/model
behavior or broad migration conclusion is made. Full logs/receipts are in
[`formal/`](formal/) with exact-file hashes in `formal/SHA256SUMS.txt`.
