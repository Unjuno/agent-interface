# Explicit input dependency candidate

Concrete integration blocker: the retained Calc recipe replaces bridge.check,
backend.key_state and bridge.keyboard temporarily to prevent Save after a visual
dependency change. This local candidate adds a single explicit public Python
input_guard context on the same owner/bridge. It protects a fixed alias, offset
and keyboard tail, rejects changed programs, and checks after existing capture/
reference validation and before every protected new key press. Other aliases
keep the existing route. Callback failure cannot authorize replay or renewal.

The callback receives copied native source and RGB, returns exactly True or
refuses, and is trusted synchronous caller code. It must bound its own I/O;
there is no interruptible callback hard deadline or hostile-code sandbox.
After it returns, association, active input, review/recovery state, lease and
same-source freshness are rechecked. The original target resolver is mandatory;
additional checks never replace it. Releases bypass callbacks, including cleanup
after a modifier was pressed. Checks retain per-stage source/timing/error records.
No callback or extra capture is added to the unregistered default route.

This is a concrete correctness/integration exception to Issue57 sequencing,
not an isolated feature sweep, sensor, scheduler, model routing mechanism or
speed experiment. Inert captures/emissions exercise real bridge/backend paths.
The initial red tests, later focused results and complete native suites are
retained. A local contract PASS is insufficient for production adoption.

Next gate: adapt the previously frozen Calc recipe in a separate successor,
without modifying old evidence; primary-use one normal and one wrong-entry case
with fresh explicit modal review/grounding and post-terminal workbook scoring.
Freeze source/order/attempt limits before those allocations. Retain failures.
Do not push or change defaults based solely on these contract tests. Full goal
remains active and no speed, token savings or human-tempo claim is established.
