# Issue #6301 T0 successor — preparation record

Historical preparation snapshot for the expired requested WSLc allocation 02; that allocation remains unconsumed. Current formal result for fresh OrbStack allocation 03 and audit-only allocation 04 is recorded in [`ALLOCATION_03_04_RESULT.md`](ALLOCATION_03_04_RESULT.md). This file retains its original preparation facts for provenance; it is not the current status.

## Question and scope

Correct the finite renderer defect where a current-generation `NOT_APPLIED_VERIFIED` receipt was described as “Effect not verified,” while preserving task-terminal status as a separate conjunction of current effect, verification, release, collateral status, and every required obligation. This is synthetic method validation only; it makes no model, GUI, live-runtime, safety, or product claim.

## Frozen inputs and construction

- Main base: `c80e98614720c95dc68a6a48e2d057ae6e94b98e`.
- Original fixture copied byte-for-byte from predecessor commit `eba652642a7a741d57bbdfe0c1a9929d3b15bd7f`; SHA-256 `35bfa13d5edee93d834ddc54c980bb24a48b8a5bb9a4e9bcc9dcddd11d1b51a9`.
- The fixture contains 9 top-level traces, 10 distinct task rows because `independent_next_task` has two tasks, and 30 display records across A/B/C.
- Candidate, independent auditor, construction-test, and runtime image identities are recorded in `FREEZE.json`.
- A first host-only construction run exposed the original 27-count arithmetic error (6/7 tests). The count was corrected without changing fixture bytes or semantic conditions. The corrected host-only construction suite then passed 7/7; a further test was added to assert rejection of all four frozen mutations, and the suite now passes 8/8. This is preparation evidence, not a WSLc/container experiment or formal candidate result.

## Planned execution gate

The only requested interval is 2026-10-02 00:35–00:43 UTC and is not a grant. Do not invoke a WSLc container unless the preceding #5927 owner explicitly releases its slot, the coordinator explicitly confirms this exact allocation, and immediate checks confirm current main/source/image identities, no path/output collision, and a known-empty WSLc container inventory. The intended formal sequence is one CPU-only, network-disabled candidate, followed only on candidate exit 0 by one separate raw-only auditor. Retries are zero. Use the cached pinned Python image with pull disabled; keep source/input mounts read-only and write only to a fresh output mount. WSLc does not expose a read-only rootfs switch, and its cgroup/swap warning precludes a hard memory+swap claim.

## Current evidence and counts

- WSLc 3.0.1.0 / kernel 6.18.40.1 identified; cached image digest and ID inspected read-only.
- WSLc container inventory was empty at the last read-only check.
- Candidate: 0; formal auditor: 0; retries: 0; GPU/model/GUI/input: 0.
- Result: not yet available. The allocation remains unconsumed and cannot be called PASS or FAIL.
