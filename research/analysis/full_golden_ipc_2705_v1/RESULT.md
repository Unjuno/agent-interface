# Result: full golden IPC allocation v5

Status: `HOLD_TASK1_EFFECT_NOT_REACHED`.

The local Docker route passed the container preflight, launched the pinned GUI
runtime, and completed a host-local `codex.exe` model call through the shared
volume IPC broker. The model remained non-authoritative. The first task did not
produce an independently scored effect: the browser remained at `task-1 READY`
after the submitted navigation/action sequence. The existing persistent route
therefore stopped fail-closed at `reuse route requires cached target` before
task 2 reuse.

This is not a six-task success and is not evidence against the IPC boundary.
The exact allocation is retained locally under
`runtime/results-local/full-golden-ipc-2705-v5`; it must not be retried. Any
action/route correction needs a new successor allocation and preregistration.

The earlier v1-v4 attempts stopped on missing Docker GUI dependencies
(`openbox`, `wmctrl`, or Python `openpyxl`) and are infrastructure setup
failures, not selected away results.
