# MAP01 v10 — 15-second observe-refresh experiment

This directory tests the concrete lease-refresh idea from Issues [#4513](https://github.com/Unjuno/agent-interface/issues/4513) and [#4516](https://github.com/Unjuno/agent-interface/issues/4516). The objective is the experiment; branch/PR work only publishes its evidence.

## Result

The scoped hypothesis is supported for the one formal allocation at seed `990637`: the sole effective-controller change was the observe-only refresh deadline from 5s to 15s, and all three observed inter-segment refreshes were admitted and completed. Nine model-authored primary action programs completed after fresh observations. All 27 recorded owner releases verified empty.

The complete 24-decision formal allocation is **`HOLD_INCOMPLETE_24_DECISION_CLOCK_BOUNDARY_ERROR`**. It stopped at decision 8 with `ValueError: controller decision precedes observed boundary`; eight model turns completed and the next was interrupted. No final report or score exists. This is neither a gameplay FAIL nor evidence that MAP01 was exited. The exact causal timestamp/invalidation boundary remains unresolved.

The previous seed `990636` was a separate, consumed `STOP_CONTAINER_SOURCE_MOUNT_INCOMPLETE` before gameplay. Its failure exposed a sparse-worktree source-mount omission. It was never retried. A separate zero-model startup smoke then passed with 3/3 verified empty releases.

## Evidence and reproduction

- [H/T/D/C/U freeze for formal seed 990637](FORMAL_FREEZE_990637.md)
- [Formal STOP/HOLD record](results/map01-model-loop-finite-v10-20260927-02/STOP_RECORD.md)
- [Read-only machine audit and full raw-file SHA-256 map](results/map01-model-loop-finite-v10-20260927-02/V10_RESULT_AUDIT.json)
- [Exact runner exception](results/map01-model-loop-finite-v10-20260927-02/runner-exception.txt)
- [Frozen generated effective controller](frozen-source/effective-controller-990637.py)
- [Prior source-mount STOP record](results/map01-model-loop-finite-v10-20260927-01/STOP_RECORD.md)
- [Successful zero-model startup preflight](preflight/container-startup-zero-decision-20260927-01/)

Run the read-only audit with:

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/map01_model_loop_finite_v10/audit_result.py
```

The pre-allocation pinned-container tests were 5/5 existing controller/HUD tests and 3/3 new Executor lease boundary tests. The startup smoke used zero model turns, reached the session-ready event, completed two observe-only controls, and verified every owner release empty. These are construction/regression gates, not substitutes for the formal episode.

The exact one-time formal command and all identities are in [FORMAL_FREEZE_990637.md](FORMAL_FREEZE_990637.md). Never rerun seed `990636` or `990637`, or reuse either consumed result directory.
