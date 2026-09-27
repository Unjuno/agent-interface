# #3066 live X11 runtime dependency/fault allocation v2 — retained STOP/HOLD

Allocation `safety-graph-live-x11-3066-20260923-01` was source/hash-frozen before formal execution. The sole formal orchestration was terminated by the outer execution-tool timeout after **6/14 complete cases**. It was not resumed, rerun, replaced, or pooled.

## Disposition

- execution: `STOP_OUTER_EXECUTION_TIMEOUT`
- scientific aggregate: `HOLD_FORMAL_INCOMPLETE`
- formal invocations/reruns/replacements/post-freeze tuning: `1/0/0/0`
- complete cases: 6; partial directories: 0; unstarted: 8
- aggregate `RAW.json` was never produced by the consumed runner
- no owned Xvfb/Openbox/app/worker process remained at post-stop inspection

The frozen raw auditor run over the **incomplete prefix** is retained as `PARTIAL_AUDIT.json`. Its decision is diagnostic only; the missing 14-case denominator prevents treating it as the preregistered aggregate scientific verdict.

## Prefix observations, not rates

The six complete bare-Xvfb rows include two independently observable safety counterexamples to the all-fault PASS condition:

1. `bare/display_stall`: Tk KeyRelease occurred about 50.58 ms after the 150 ms authority deadline, slightly beyond the frozen +50 ms grace.
2. `bare/cleanup_failure`: the injected backend release failure left F8 down at the independent XQueryKeymap observation. Fixture cleanup released it only afterward.

These rows are preserved exactly and are not discarded because the allocation stopped. They do not provide a balanced two-configuration denominator or a reliability rate.

`target_replacement` reached a neutral keymap but had no independent Tk KeyRelease timestamp after the target app was terminated, so timely release cannot be reconstructed from that row alone.

## H/T/D/C/U scope

The frozen H/T/D/C/U remains in `PLAN.md`. The executed runner is an explicitly disclosed method-preserving Xlib/XTEST slice of current-main `X11Backend` focus/key/release semantics, with complete upstream backend/session/contract Git blob IDs pinned in `SOURCE.json`; it is not execution of every runtime module. No Docker/OrbStack engine was available. No model/provider, external network experiment, user desktop, or production runtime mutation occurred.

This STOP/HOLD preserves the evidence needed for a fresh successor allocation only if the scientific question remains valuable. The consumed allocation ID must not be resumed.
