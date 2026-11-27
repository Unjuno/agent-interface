# Local Linux pidfd process-only trial — R02

**Disposition: PASS_PROCESS_SIGNALLING_SCOPED.** One new owned Xvfb process,
one invocation, three predeclared schedules. This validates only the current
pause helper's process-signal path on this local Ubuntu WSL2 host. No X client,
XTEST/SendInput call, keyboard/button input, or application task was executed.
No WSLc allocation, Docker operation or package/image installation was used.

The [R01 first failure](../xvfb_pidfd_live_20261023_r01/README.md) is unchanged.
R01's pathname-readiness predicate failed before the signal schedules. R02
changed only the process-only preparation criterion to two independent live
process-state observations around a 300 ms settle interval, and added a frozen
Xvfb executable hash check. It does not replace X-connection readiness for a
GUI trial. `pathname_socket_present=false` in this result is retained.

## Outcome

| Schedule | Actual signal calls | Independent state observation | Result |
| --- | --- | --- | --- |
| Healthy 500 ms resume timer | STOP, CONT via pidfds for owned PID 379 | T while stopped, S after resume | Scoped pass |
| Injected status-read error after STOP | STOP, CONT via the same owned process identity | S after exception cleanup | Scoped pass |
| Injected timer-start error after STOP | STOP, CONT via the same owned process identity | S after exception cleanup | Scoped pass |

Signals were real Linux syscalls; the two faults were declared dependency
injections. Only the healthy schedule has a separate independent stopped-state
sample. Both fault schedules have accepted STOP/CONT calls and independent
live/resumed-state readback, not an independently measured stop duration.
Every readback retains raw `/proc` status/stat, monotonic time and PID. The
signal trace records pidfd `fdinfo`; the audit checks PID plus process start
ticks across the observations. PID reuse itself was not induced.

The signal-invocation intervals were 507.370269 ms, 0.043619 ms and 0.064604 ms,
respectively. These are descriptive intervals between request invocations,
not input-neutralization latency, a real-time bound or a performance result.

The launcher resumed/terminated only its owned target through a retained
cleanup descriptor and reaped it with exit code 0. A separate later query
found PID 379, the `:88` lock and pathname socket absent. Outer `wsl.exe` exit
was 0. The first result was not rerun.

## Source and retained evidence

- Probe source `6c84826f1ec127e3ab95b259a4e6fff46a32a97f`; conditions frozen at
  `d0e8ea208` before execution. The target helper is the PR #9420 implementation.
- `conditions.json` preserves question, binary/source digests, schedules,
  command, stopping rule and scope before execution.
- `attempt-started.json` / `process-started.json` preserve first entry and exact
  owned child identity before signalling; `result.json` preserves all traces.
- `raw-launch.json` preserves outer status/stdout/stderr. `xvfb.log` preserves
  the pathname-listener/XKB warnings. No shared directory mode was changed.
- `cleanup-recheck.json` preserves post-run absence. `audit.py` independently
  reconstructs the 27 checks in `audit.json` without signalling or launching
  anything. `ast-audit.json` verifies the function AST with Python 3.12;
  `SOURCES.json` and `SHA256SUMS` bind source and packet bytes.

The first host-side AST comparison used Python 3.11, whose FunctionDef AST
serialization lacks Python 3.12's additional fields. It did not match even
though the normalized source digest did. A read-only Python 3.12 audit matches
both the original source and AST hashes. This was an audit portability repair,
not a trial rerun or a change to the retained result.

The executable helper function was compiled directly from its frozen AST with
standard-library dependencies; the GUI integration module was not imported.
This avoids dependency installation and does not count as running the full
standard-caller GUI fixture.

## Remaining goal

The helper prerequisite is now tested with real Linux signals in one scoped
trial. This is not proof of blocked-I/O input release, native target authority,
late queued-input exclusion, a live task/MAP01 effect, matched efficiency or
reliability. Actual GUI qualification still needs its real connection/readiness
and owned input-domain evidence. Verified-unused WSLc execution remains pending;
this local WSL2 run does not consume or release any WSLc slot.
