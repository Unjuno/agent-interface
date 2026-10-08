# Issue #3644 — Calc window-owner process-group lifecycle

This successor tests only the lifecycle evidence gap found in #3633 formal-01.
It does not edit/rerun #3633, repeat readiness discovery as a hypothesis, or
claim a mixed-app integrated session.

## H/T/D/C/U

- **H:** In the pinned Linux/arm64 fixture, the LibreOffice launcher and
  visible Calc window-owner may have distinct PIDs but remain members of the
  launcher’s isolated process group. A single signal to only that group can
  terminate all captured members, remove the Calc XID, and leave an unrelated
  process group untouched.
- **T:** One fresh OrbStack/Docker allocation. Launch private Xvfb, an
  independent sentinel in its own session, and LibreOffice Calc in a dedicated
  session. Record PID/start-time/PPID/PGID/SID/cmdline for launcher and visible
  owner; snapshot all launcher-group members. Send one SIGTERM to that group,
  then observe PID+start-time disappearance, XID disappearance, sentinel
  survival, direct-child reaping, and X socket cleanup. Run the independent
  auditor in a separate read-only-source/raw container.
- **D:** PASS only if group membership and identity are established, all
  captured group members disappear, Calc XID is no longer visible, the
  sentinel survives until explicitly stopped, Xvfb/socket cleanup is verified,
  and independent audit succeeds. Explicit process/XID/sentinel counterexample
  is FAIL. Missing or contradictory lifecycle evidence is HOLD; missing Calc
  readiness before the lifecycle gate is STOP.
- **C:** Same image and Calc launch recipe as #3633 formal-01. The tested change
  is lifecycle accounting/termination of one isolated process group only.
- **U:** No arbitrary daemonization, host failure, non-X11 compositor,
  physical-input, Windows/macOS, controller, effect, or #2499 long-session
  conclusion. Even a PASS here is only a prerequisite for a later successor.

Frozen allocation and results are in `FREEZE.json` and `evidence/formal-01/`.

Pre-allocation readiness smoke (`smoke_private_calc.py`) observed launcher PID
10 and Calc window-owner PID 33 in PGID 10. It only checked private Xvfb/Calc
readiness and did not signal the group; it is not formal outcome evidence.
