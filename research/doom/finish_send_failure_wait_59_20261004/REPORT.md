# H/T/D/C/U — skip child wait after failed finish send

- **H:** After merged helper `send_failure_finish` times out or errors on the owned child stdin pipe, a five-second `child.wait` delays forced child retirement and planner close even though the finish message was not sent.
- **T:** Against exact `origin/main` source at `63980603e4bb6e4b128ed07af3bf7023bc2d4734`, fill a real, text-mode child stdin pipe to EAGAIN while the child sleeps without reading; trigger cleanup; require cleanup to retire the child and close the planner within 3.5 s without probe rescue. Then retain the existing five-second wait only when the finish send returns successfully.
- **D:** The frozen red run fails at 3.54 s: cleanup is still waiting after `finish_send` failed, and the probe must kill the owned child. Three frozen green passes measured 0.256 s, 0.259 s, and 0.258 s; receipt reports finish-send failure and child exit; planner is closed; primary exception identity survives; no probe kill is needed.
- **C:** This is a constructed full-pipe teardown case using one inert Python child. It does not cover live controller/game behavior, physical input release, descendants, protocol delivery, or a universal deadline. WSLc warned that swap/cgroup enforcement is unavailable; limits are recorded as requested only.
- **U:** The follow-up skips the finish-dependent wait only after send failure, polls the owned child, then performs existing terminate/wait/kill fallback. A successful send retains the prior graceful wait path.

## Provenance and validation

The baseline source is frozen at `baseline/doom_controller_failure_cleanup_v1.py`; repaired source is `candidate/doom_controller_failure_cleanup_v1.py`. Both are bound by `FREEZE.json`, as are the POSIX real-child regression and WSLc runner. `red-run/` and `green-run/` preserve exact argv, stdout, stderr, and exit codes. `red-run-01/` preserves the first equivalent red observation before adding a platform skip and explicit stdin close to the maintained test; it is not used for the final freeze audit.

Adjacent checks: 5 cleanup helper tests, 7 wait-loop tests, and 2 controller behavior tests passed. The POSIX real-child test passed in WSLc and is explicitly skipped on Windows because this constructed nonblocking pipe setup requires POSIX semantics. 13 source-refresh tests passed on the same branch. Python compilation and scoped `git diff --check` passed.
