# Golden desktop demo v2 candidate

V2 transfers the typed persistent planner boundary from the MAP01 controller to
the ordinary six-task desktop path.  It preserves the v1 GUI runtime, adaptive
acquisition caller, target revalidation, independent scorer, and retained v1
evidence.

The fresh schema preflight remains a separate no-GUI compatibility call.  After
that gate, cold layout-A grounding and layout-B repair share one capability-
minimized app-server process and thread.  Each grounding has its own turn ID,
which becomes the existing caller's unique `call_id`.  Per-call accounting uses
app-server's `last` usage rather than its cumulative total.  The existing strict
grounding validator still runs after the adapter's JSON Schema validation.

```bash
bash runtime/golden-demo-v2.sh doctor
bash runtime/golden-demo-v2.sh run
```

Five offline tests cover the unchanged report gate, one-thread/two-turn
identity, unique call IDs, per-turn usage conversion, workspace/contract
refusal, and the explicit capability-minimized command.  The v2 doctor passes
all thirteen Linux/X11, browser, Python, Windows executable, and Codex checks.

No live task or performance result exists yet.  Freeze one run with retained v1
seed 991030.  Require 6/6 independently exact tasks, the same
cold/reuse/reuse/repair/reuse/reuse route, zero old-layout pointer admission,
verified release, one grounding thread and two distinct grounding turns.  Treat
v1 timings and usage as a sequential same-host reference, not a randomized
population comparison.

## First frozen allocation

`golden-desktop-app-server-v2-live-01` is retained as a dependency failure.  Its
fresh schema preflight completed and the minimized app-server created one
grounding thread, but no grounding turn or GUI task began.  The pinned
`runtime/.venv` lacked `openpyxl`, which the GUI suite imports; the process
exited before publishing readiness and the wrapper surfaced `StopIteration`.

The existing doctor checked PIL, NumPy, Xlib, and jsonschema but not openpyxl,
so it incorrectly passed this environment.  Do not retry this allocation.  A
new version must pin openpyxl and make doctor import it before any model call.
