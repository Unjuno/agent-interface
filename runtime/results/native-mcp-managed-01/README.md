# Managed MCP startup: bounded live composition

The primary assistant used one persistent MCP SDK stdio connection to start a
private Inkscape allocation, inspect its returned image and public goal, submit
an explicit move/save decision, and read terminal process status. No sensor
development, delegated agent or Docker restart was involved.

Two native_start calls returned starting then ready for the same harness PID
16839. One action program emitted 43 input operations. Independent saved SVG
inspection found x=86, y=50, width=40, height=30 with no transform; task scoring
passed, feedback matched and the cleanup receipt reported completed. Input
release was verified empty. Separately, native_status reported return code 0,
while deliberately leaving task_success null and cleanup_verified false.

Run `python3 runtime/results/native-mcp-managed-01/audit.py` from the repository
root. The offline audit checks 48 manifest entries, both exact MCP image blocks,
request/reply identity, saved geometry, release evidence and terminal owner
status. PLAN.md precedes the run; client.py retains the SDK driver. The manifest
covers the original archive entries, not this README or the later audit script.

Source snapshots are post-run: the managed-submit ownership precheck was added
after the live run and covered by an inert failed-start protocol test. The
successful live run therefore does not directly exercise that final addition.
The final related local suite passed 44 tests.

This used a shell-launched SDK bridge and a primary-authored decision file, not
tools registered in the current Codex host. It proves this bounded composition,
not lower latency, fewer model tokens, crash/disconnect cleanup, cancellation,
or general application reliability. Startup readiness returns the retained
initial frame; it is not an assertion that the frame remains current.
