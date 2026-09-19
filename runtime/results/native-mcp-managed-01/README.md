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

## Timing boundary audit

`python3 runtime/results/native-mcp-managed-01/timing.py` partitions the existing
same-host monotonic timestamps without changing the archived run. The exchange
interval is 1133.463 ms: entry to request commitment 118.880 ms; commitment to
harness action entry 23.539 ms; action entry to input execution 251.814 ms;
input execution 395.886 ms; feedback call 71.853 ms; window review 64.316 ms;
and remaining bookkeeping/finalization intervals as emitted by the script.
Input execution includes explicit waits. Action-entry preparation includes
multiple operations and must not be attributed to any one guard or capture.

The feedback record finished 871.707 ms after exchange entry, but this is a
title/image cue retained inside the harness. It was not streamed to the model
at that time and is not first useful feedback or semantic completion latency.
Exchange return is also before MCP content encoding, SDK delivery and model
interpretation. The final 180.421 ms combines evaluation, cleanup, publication,
polling and result preparation without separate timestamps. This single record
cannot identify a general bottleneck or a causal improvement. timing.py is an
additional analysis script, outside the original evidence manifest.
