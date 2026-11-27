# Public MCP observation on a private local Xvfb — R01

**PASS_OBSERVATION_SCOPED.** One new authenticated Xvfb on display `:188`, one frozen invocation, two predeclared fixture draws. Both public `interface_observe` calls returned 64×64 PNGs with all 4,096 pixels exactly red and then green. Both retained `interface_results` calls returned identical PNG bytes with `operation_invoked=false`. The same persistent session was reused and closed with `release_attempted=false`. No input tool was called.

The source was committed at `e06535d5c`; conditions were committed at `89a976356` before the attempt marker. Base main was `706e28bdcbfd3cfc4dc95df2dbf63107c8d10958`. [conditions.json](conditions.json), [SOURCES.json](SOURCES.json), [pip-freeze.txt](pip-freeze.txt) and the wheel/install report preserve source, dependency and environment scope. The previous ephemeral `/tmp` venv and setup receipts disappeared across a WSL restart before this formal attempt; construction was repeated in a persistent home-cache venv, with receipts written directly here. No formal attempt was repeated.

## What changed in the evidence

The preceding Linux pidfd R02 packet tested process signalling without an X connection. This packet establishes a successful authenticated X connection, fixture rendering, real X11 capture and public MCP presentation in this PC's newly prepared dependency environment. It does not improve on earlier Xvfb task/release results or establish a new control mechanism.

For both samples, raw monotonic timestamps satisfy fixture `sync` return ≤ public invocation ≤ native capture start ≤ native capture end ≤ public return. This is an ordering discriminator after a known application commit; it is not a redraw acknowledgement for arbitrary applications, an input-caused effect latency, a performance comparison, or a hard deadline. The app-rendered fixture state was intentionally known to the probe.

The [offline auditor](audit.py) reconstructs the PNG filters and complete RGB pixels with Python's standard library, separately from the backend/Pillow conversion. It checks images, artifact hashes, public retained replies, request count, session reuse, timestamps, no-input report fields, close and cleanup. Its [19 checks](audit.json) pass, including rejection of deliberately corrupted PNG bytes. The auditor was written after execution and does not independently observe the live server.

## Raw and cleanup

- [result.json](result.json), [launch.json](launch.json) and stdout/stderr retain the first outcome and actual process exit.
- `observe-*-reply-0.json`, `retained-*-reply-0.json`, and `mcp/` retain literal public messages, requests, reports and PNG artifacts.
- [process-started.json](process-started.json) retains PID 372, pidfd receipt and process start ticks. Owned pidfd TERM/reap returned exit 0.
- A separate [cleanup readback](cleanup-recheck.json) found the old PID, display lock and pathname socket absent. It does not assert system-wide resource emptiness.
- `xvfb.txt` preserves server warnings. The pathname listener warning did not prevent the actual authenticated connection and observations; readiness was established by these connections, not by socket-file existence.
- Xauthority lived only in the probe's private temporary directory and was removed; its cookie is not published. TCP was disabled. Only this child and its clients were closed.

## Limits and next action

This is native Ubuntu WSL2, **not WSLc or Docker**; WSLc allocations consumed: zero. The user selected this PC; no Windows desktop input, pointer warp, key/button input or target-task action occurred. Two observations in one run are not repeated reliability evidence. MAP01, independent input-caused task success, blocked-I/O release, finite task recovery, provider/model accounting, matched efficiency and the overall goal remain open.

The next live control step should use another fresh owned Xvfb and a separately frozen protocol for the repaired blocked-I/O test, with actual call/return and independent effect-readback timestamps. Keep this observation-only result and the previous process-only failures unchanged. Do not promote this packet to task success.
