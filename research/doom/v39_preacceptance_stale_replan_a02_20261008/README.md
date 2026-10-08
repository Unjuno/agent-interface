# Pre-acceptance stale-sequence controller recovery A02

Offline construction experiment for the current-main V39 MAP01 controller.
Prior evidence inspected the production `execute_segment` source and found that
it raises on every executor rejection. A02 executes that exact nested
production function with a deterministic fake rejection, then exercises a
bounded recovery candidate against the exact production `wait` and
`begin_model_turn` functions.

## H/T/D/C/U

**H.** When the executor rejects a not-yet-accepted action specifically because
its `expected_sequence` is stale, the controller can record that candidate as
discarded without input, consume a strictly newer complete observation, and
start one new planner turn grounded in that image and paired health/ammo. Other
rejections, process exit, timeout, malformed or stale observations, and changed
pointer binding must fail closed. No rejected action may be resubmitted.

**T.** Pin current controller, executor, and planner adapter. Extract and
execute the production `execute_segment` with a fixed stale-sequence rejection
and assert its current behavior (one submit, zero admissions, immediate
exception). Then replay a typed observation, exact rejection, and newer full
observation through production `wait`, and start a candidate turn with
production `begin_model_turn`. Test fail-closed controls.

**D.** Pass only when the extracted production branch reproduces its current
rejection failure; candidate consumes the exact rejection and a new complete
observation using production `wait`; adapter receives the new sequence image
and paired signals; no submit occurs after rejection; and every negative
control refuses without opening a planner turn.

**C.** The rejection may be too rare or too late to matter in live use. A
freshly returned observation can still be stale by the time a planner answer
arrives, which existing final admission must continue to reject. This
construction says nothing about event frequency, latency, live input release,
or task effect.

**U.** Synthetic event ordering and planner client only. No App Server, model,
game, GUI, OS input, live threat, formal allocation, or physical release
measurement ran. Result reproduces the source-bound no-recovery defect and
tests a candidate composition; it is not a production fix, live recovery
result, or Issue #59 completion. The shared Issue #59 live allocation remains
unassigned and untouched.

## Reproduction

Executed on Windows 10.0.26300 with CPython 3.11.9 (64-bit). Both runner and
independent verifier were run normally and under `-O`; raw outputs and exit
codes are retained in this directory.

From repository root:

```powershell
python research/doom/v39_preacceptance_stale_replan_a02_20261008/run.py
python -O research/doom/v39_preacceptance_stale_replan_a02_20261008/run.py
python research/doom/v39_preacceptance_stale_replan_a02_20261008/verify.py
```

The freeze records exact Git blobs. The harness never launches the controller,
executor, game, or OS input; it extracts only the named production functions.
