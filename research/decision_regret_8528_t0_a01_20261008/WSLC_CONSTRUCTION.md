# WSLc construction portability check — Issue #8528 T0 A01

This is a post-result construction/reproduction check. It does not rerun either formal command or alter the frozen scientific result.

## Frozen inputs and execution

- Formal source freeze: `b423c53b87530eaa798355a96fd441088af5ad4f`.
- Result package: `3f6bc41adaaf6dcc96ff0fd0deea5c691140c8d8`, read from the local package whose formal results are merged in PR #8542.
- WSLc image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Local image metadata reports Python 3.12.14.
- Read-only bind mount of the result package to `/src`; network disabled, pulling disabled, one CPU requested, 512 MiB memory requested, and the container removed after exit. No Docker Engine was used.
- Executed the two construction suites in normal and optimized Python. The candidate and auditor CLI entry points were not invoked; formal counters remain exactly 1/1 each.
- All 11 candidate+auditor tests passed in normal mode and all 11 passed under optimized Python. Exact stdout is retained in `WSLC.stdout.txt`.

## Resource/interpretation limit

WSLc printed: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Accordingly, this record does not claim verified memory/swap enforcement from the requested resource flags. The finite CPU-only tests finished in under a second per suite. They use no model, GUI, human, game, network service or OS input.

The read-only package's existing SHA256SUMS verified 15/15 immediately after the WSLc run, and no task-named container remained in the WSLc container listing. This is cross-environment construction reproducibility, not a new formal T0 result, live threat exposure, or evidence of real-task utility.
