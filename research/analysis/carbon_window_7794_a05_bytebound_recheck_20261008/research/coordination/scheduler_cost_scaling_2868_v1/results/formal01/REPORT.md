# Issue #5021 — formal01 result

**Decision: `FAIL_HEAP_COST_THRESHOLD_NOT_MET`.** This is the preregistered
threshold outcome, not a platform-independent conclusion about heaps.

## Executed experiment

- Allocation: `scheduler-cost-scaling-2868-v1-20260928-01`.
- Source base/freeze commit: `1b1b683a07b87edba6fb312600f09d28ea86b4ae` /
  `ddd43cc509b71fe1886af666ac00dde214952b43`.
- Environment: OrbStack Docker, Linux/arm64, Python 3.12.14, image
  `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`;
  network disabled, read-only root/source, 0.25 CPU, 512 MiB, 64 PIDs.
- Runner: one container invocation; exit 0; 225/225 fresh worker processes
  returned a row. No retries. Raw SHA-256:
  `0b7479954f0515849ad7c2f285675740229a20fdb2114d4e37fa4ee8576449d9`.
- Independent raw-only audit: one separate container invocation; exit 0;
  `errors=[]`; all 12/12 corruption controls rejected.
- Full traces from all three implementations exactly matched the frozen
  `(-priority, deadline, enqueue_seq, op_id)` oracle in every paired block.

## Timing result

Median paired per-process CPU ratios (heap divided by baseline):

| Queue size | vs linear min-scan | vs sorted list | Required |
|---:|---:|---:|---:|
| 512 | 0.5701 | 10.4488 | both ≤ 0.80 |
| 2048 | 0.04794 | 2.2594 | both ≤ 0.80 |

The heap met the threshold against linear scanning, but missed it against the
sorted-list baseline at both required sizes. Median CPU times at 512 were
2.100 ms (heap), 3.544 ms (scan), and 0.182 ms (sorted list); at 2048 they
were 2.758 ms, 55.985 ms, and 1.246 ms respectively. The preregistered outcome
therefore remains FAIL; thresholds were not changed after seeing the data.

## Interpretation and limits

The exact frozen `runner.py` imports `heapq` inside `execute()`, which is called
after the timer starts. Thus the first `heapq` module import is charged to every
heap worker, while the built-in list/sort arms have no analogous module-load
cost. At small sizes the approximately 1.8–2.0 ms heap-arm median strongly
reflects that implementation/setup cost. The measurements remain the exact
outcome of the registered implementation and gate, but they do **not** isolate
steady-state data-structure operations cleanly. No post-result patch or rerun
was made. Any corrected timing boundary requires a separately frozen
successor allocation; the present raw FAIL is preserved unchanged.

This is one synthetic all-ready queue family, five sizes, 15 fixed paired
blocks, one OrbStack/linux-arm64 host, and a pure-Python implementation. It
does not test waiting/dependencies/resources, dynamic reprioritization,
cancellation, starvation policy, real desktop queues, other languages,
production task latency, or product benefit. It does not support adopting a
heap or sorted list in the runtime.

## Reproduction/evidence

Exact runner/auditor argv and source/image hashes are in `../../FREEZE.json`.
`CONTAINER_RUN.json` and `AUDIT_CONTAINER_RUN.json` preserve the invocation
receipts. Verify the retained files with the adjacent `SHA256SUMS` manifest.
