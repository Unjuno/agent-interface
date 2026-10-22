# V39 paired-source recovery repair finding

## Question
Does a current-main V39 cover monitor advance its coherent-pair watermark after a newer health/ammo pair passes the guard, so recovery can finish after a previous hard invalidation?

## Finding and repair
The retained `cover-5` trace provides the invalidation and reconciliation case. Its admitted health source is 61 at sequence 166 with authored effective `hard_minimum=51`; typed sequence 218 reports health 48 and ammo 37. The exact later artifact observation matches the typed epoch, pointer binding, RGB hash, and signal values. Current-main invalidates the typed crossing, then reconciles the artifact duplicate. In the minimal offline reproduction, a synthetic newer pair at sequence 219 with health 51 and ammo 37 passed both guards, but the success path did not update `last_pair_sequence`; `recover_coherent_source_after_observation` could not observe the fresh pair and failed after its bounded wait.

The one-line repair advances `last_pair_sequence` on the normal, fully validated paired-observation path. It does not advance the watermark on hard/unknown invalidation. The same-epoch typed/full reconciliation branch remains unchanged.

## Evidence and execution
- Historical raw trace SHA-256: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- Historical report SHA-256: `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`.
- Frozen repaired controller SHA-256: `704c8c8a35f88765f207e4be18b4e32979fdcb6960aaeafcb867dcee4cb8eed0`.
- Frozen guard SHA-256: `7be055c4bd68a1528f4b2b02b543435bd64465ea42d4452f5597d6dce08442a0`.
- `test_live_trace_pair_recovery.py`: exact retained sequence-218 raw rows plus report-derived threshold; synthetic sequence-219 changed-binding/UNKNOWN and sequence-220 valid pairs. It checks hard invalidation, matching artifact reconciliation, stale-source rejection, watermark preservation on UNKNOWN, recovery only at sequence 220, and that typed-only soft evidence cannot advance the pair watermark before a matching full artifact row reconciles. Neither synthetic pair is presented as live evidence.
- New replay: 1/1 passed against pinned source copies.
- Related V39 tests: 43 passed in one combined run, including pair wait dispatch, duplicate consistency, pending observation drain, stale rejection continuation, and cover/release policy tests.
- Independent code review of the repair and the added UNKNOWN/recovery regression found no Critical, Important, or Minor issues; reviewer assessment: ready to merge with normal non-author review and integration gates.
- Initial pending-drain invocation lacked `research/live_control` on `PYTHONPATH`; rerun with the repository paths passed. This was invocation setup, not a test failure.
- WSL was present, but no `wslc` executable was found and Docker Desktop integration was unavailable in the distro. No container test is claimed.
- This is offline trace replay and code/test verification only. No Doom process, model, Executor, owner thread, or physical input was run.

## Status
Repair validated locally and recorded on the research branch. Integration into `main` remains subject to a non-author review. The authorized live/game allocation is not used or renewed by this work.
