# A02 formal-01 STOP — Issue #5692

Allocation `ui-redress-5692-x11-a02-20261001-01` was invoked exactly once using the preregistered command under a private Ubuntu-WSL Xvfb display. The run reached the final `race-after-check` row but raised `subprocess.TimeoutExpired` while waiting for the overlay child to exit (`overlay.wait(timeout=2)`). The complete candidate did not write `raw.json`; the independent auditor was not invoked. Candidate output/traceback is preserved in `formal-01.log`.

- Candidate invocation: 1; exit 1.
- Independent audit: 0 invocations.
- Complete raw output: absent; no scientific rows accepted.
- Docker/OrbStack: 0 invocations; no shared container inspected or changed.
- Disposition: `STOP_CANDIDATE_SUBPROCESS_TIMEOUT`; scientific result `NOT_EVALUATED`.
- Retry or source change within A02: prohibited. `candidate.py`, auditor, test suite, and freeze remain unchanged.

The exception names only the parent-side two-second wait. The temporary trial directory was removed by the candidate's cleanup after the timeout, so no overlay event log or child diagnostic remains to determine why the child did not exit by that deadline. No X11 recipient-boundary inference may be drawn from the in-memory rows.
