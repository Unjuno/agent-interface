# Formal allocation 01 — retained STOP

Allocation `wallclock-source-time-reversal-2442-20260922-01` was invoked exactly once. The outer execution tool terminated at its 120-second envelope before the supervisor wrote terminal END/STOP evidence.

Retained denominator state:
- expected: 34 cases / 204 captures;
- complete RESULT cases: 10;
- 11th case started and all six raw frames were retained, but no RESULT receipt exists;
- raw frames retained: 66;
- later cases unstarted;
- root END.json and STOP.json absent;
- runner/Xvfb return codes unknown and must not be invented;
- same allocation reruns: 0.

A post-stop process check found all 11 recorded producer PIDs absent and no X11 socket at :500. The owned leftover Xauthority credential was hashed, then deleted locally; its secret bytes are not published. This cleanup observation is not a substitute for the missing original terminal receipt.

The unchanged preformal auditor exits 2 / HOLD because END.json is absent. No partial rows are pooled into a scientific PASS/FAIL. Disposition is **STOP_OUTER_TOOL_TIMEOUT_INCOMPLETE_DENOMINATOR**.

Per repository failure-routing policy, the next attempt stays under #2442 and changes only execution granularity: a separately identified, prospectively frozen batch allocation. Scientific cases, candidate, thresholds and source-time semantics are unchanged. Allocation-01 bytes remain immutable and will be published losslessly with the final evidence handoff.
