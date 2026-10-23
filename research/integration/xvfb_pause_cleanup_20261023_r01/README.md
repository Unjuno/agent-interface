# Private Xvfb pause cleanup preparation — R01

Code source: `29fa6de1924fe248eec8a4f97d8ec6b05039c63d`.
Baseline: `527d7a940c23dbbb6af3831dc6705eb2a24ef096`.

The live-Xvfb test helper previously sent SIGSTOP by PID, then read `/proc`
state and started a resume timer. A status-read or timer-start exception could
escape before any SIGCONT. Its later resume also used a PID number that might
have been reused. This was found while reviewing prerequisites for the next
live run; no live process was stopped in this work.

The helper now retains a Linux pidfd before validating the declared private
`:88` Xvfb. STOP and CONT use that descriptor. Every exception after attempting
STOP attempts CONT on the same descriptor and closes it. A timer callback and
explicit cleanup share an idempotent resume operation; errors are retained in
the existing resume receipt. Missing pidfd APIs refuse before any signal, with
no PID-number fallback. The ordinary runtime backend is unchanged.

Python documents a pidfd as a descriptor referring to a process, and the
signal API sends to the process referred to by that descriptor:
[os.pidfd_open](https://docs.python.org/3.12/library/os.html#os.pidfd_open),
[signal.pidfd_send_signal](https://docs.python.org/3.12/library/signal.html#signal.pidfd_send_signal).
These API contracts support the chosen mechanism; their successful use in
this live fixture remains untested here.

## Retained evidence

- `raw-red.txt`: initial five-case suite; four failures before implementation.
- `reproduce_baseline.py` loads the frozen old helper in memory. The final
  status-read and timer-start failure cases both fail in `raw-baseline.txt`.
- `raw-normal.txt` and `raw-optimized.txt`: seven pure signal-double tests pass
  in each mode. One opt-in live integration test is skipped on this Windows
  host: unittest reports eight discovered, `OK (skipped=1)`.
- Tests cover post-STOP read failure, timer-start failure, uncertain STOP
  return, idempotent resume, retained resume error without PID fallback,
  foreign-display refusal, and missing pidfd support.
- No real signal, X display connection, WSLc/container/image operation, Docker
  operation, native desktop input or Linux test run occurred. The Linux source
  import alone does not enter its opt-in integration test.

`conditions.json`, `SOURCES.json`, and `SHA256SUMS` bind commands, environment,
canonical Git blobs and packet bytes. Prior experiment packets remain unchanged.

## Live next step

[LIVE_NEXT_RUN.md](LIVE_NEXT_RUN.md) specifies the next finite current-source
private-Xvfb test and its existing task-effect/readback checks. It is **not
executed**. Issue #7924's latest published comment still records unresolved
WSLc ownership/unused-slot confirmation. The `python:3.12-slim` digest in the
repository smoke is not a qualified Xvfb/dependency image. A specific unused
allocation and a qualified cached image must be established before container
construction or execution. A stopped Ubuntu distro does not establish either.

This repair is preparation for live release/effect qualification. It proves
neither actual Linux signal delivery nor physical input release, a deadline,
MAP01 effect, matched efficiency, reliability, or completion of computer control.
