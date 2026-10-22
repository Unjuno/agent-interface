# Construction log — pre-freeze only

## Attempt 01 — unit tests

- Commands: `python3 generate.py`; `python3 -m unittest -v test_protocol.py`.
- Outcome: fixture generation completed; two tests ran; auditor reconstruction test failed before any candidate/oracle comparison because the auditor unpacked two packed public fields into three local variables (`ValueError: not enough values to unpack (expected 3, got 2)`). One other candidate formula test passed.
- Classification: construction-code defect, not a scientific counterexample. No formal candidate, auditor, or one-shot driver invocation occurred.
- Correction: unpack `resolved_mask` and `resolved_error_mask` as two variables. The test now reaches the independent oracle mismatch assertion.

## Attempt 02 — corrected source, analytic variance refinement

- Commands: normal and optimized unittest suites, then `py_compile` on all six Python modules.
- Outcome: 3/3 tests passed in each mode; compilation passed.
- During review, corrected the exact variance for fixed stratum allocation. For 200 units in each of two strata, `Var(HT)=sum_h Var(Z_h)/800`; the earlier draft divided by 400 and would have doubled the variance. The explicit analytic-value test now fixes the expected value at `0.0019541666666666668`.
- No 20,000-cohort candidate or auditor run occurred before freeze. Formal invocation counts remain zero.

## Resource/preflight record

- Working task directory is not a Git checkout; remote additive branch is `research/7993-ipcw-repeated-uncertainty-a01-20261005`. It was created from `1eac6ea9f5b91cc10a8c3dc20374b9d79ffcf179`, then fast-forwarded before freeze to latest main `d3a51bc4c962b223d05280225042b96a033df8bf` after unrelated #59 main advancement; no research source or formal invocation existed at fast-forward.
- `docker context show` returned `orbstack`; `docker info` returned server `29.4.0 linux/aarch64`.
- Read-only `docker image inspect python:3.14-slim` returned image ID and RepoDigest `sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151`.
- `wslc.exe` is not installed/on PATH. No pull, prune, restart, or VM operation was attempted.
