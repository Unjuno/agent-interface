# Standard-caller effect timing and recovery — R01

**Run:** `AI-XVFB-CALL-EFFECT-TIMING-20261022-R01`

**Disposition:** `PASS_TARGET_TEST_WITH_LAUNCHER_STATUS_CAVEAT`

**Code source:** `0dba975b22fdbdf43f8981b56b0e74b1e8ca7382`; the timing test blob is recorded in [SOURCE_BLOBS.txt](SOURCE_BLOBS.txt). Freeze packet commit: `b14526cba8`. The only tree difference from code source to freeze commit is this run packet; `git diff 0dba975b22fdbdf43f8981b56b0e74b1e8ca7382 b14526cba8 -- runtime` was empty.

## Outcome

The exact test subprocess exited `0` and unittest reported `Ran 1 test in 9.363s / OK`. Its retained JSON contains one fresh-session `c` KeyPress with an application-effect commit timestamp, and an independent PowerShell audit of the JSON passed all listed predicates in [audit.json](audit.json).

| Measurement | Result |
|---|---:|
| Public cancel tool invocation → return | 95.283 ms |
| Cancellation admission → response | 95.066 ms |
| Supervisor release operation start → supervisor readback | 0.193 ms |
| Cancellation admission → supervisor release readback | 79.809 ms |
| Cancellation admission → KeyRelease request | 79.633 ms |
| Cancellation admission → independent all-up readback | 108.282 ms |
| Fresh input invocation → app KeyPress receipt | 37.701 ms |
| App KeyPress receipt → effect commit after `app_display.sync()` | 0.097 ms |
| Effect commit → independent property readback complete | 4.937 ms |
| Fresh input invocation → independent effect readback complete | 42.735 ms |
| Fresh input return → independent effect readback complete | 1.925 ms |
| Delayed-request horizon | 8,504.174 ms after cancel start; no late `b` press; all `a/b/c` keys up |

The owner was blocked in its real Xlib `Display.sync()` path. The prestarted supervisor issued one release, read its state back, and a separate parent X client observed `a` and `b` up. A distinct fresh session and target then completed the synthetic `c` action; its app property changed as expected and was independently read back. The synthetic task oracle passed.

The old cancellation remained `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`, and `late_server_request_possible=true`. The fresh synthetic oracle is not promoted to runtime task success, and this observation does not authorize replay or prove the old server queue is empty.

## Conditions and environment

This was one local Ubuntu 24.04.3 WSL2 trial using Python 3.12.3 and a private Xvfb display `:88` (1024×768×24, TCP disabled). Xvfb package version was `2:21.1.12-1ubuntu1.8`; the exact executable SHA-256 is in `result.json`. Direct dependency pins match the repository workflow; all installed transitive versions are preserved in [pip-freeze.txt](pip-freeze.txt). The complete pre-run conditions are [CONDITIONS.json](CONDITIONS.json).

WSLc and Docker were not used. The Docker Desktop WSL distro was not invoked. No model ran and there was no matched baseline.

## Status caveats and limits

- The test subprocess exit code is recorded as `0`, and its raw log ends in `OK`. However, the enclosing `wsl.exe` invocation returned `1`; a later benign `bash -lc 'exit 0'` diagnostic also returned `1` through this host wrapper. See [launch-wrapper.json](launch-wrapper.json). The wrapper status is therefore unreliable here, but it is retained rather than silently replaced with the test's status.
- `xvfb.log` reports failure to create a pathname UNIX listener plus nonfatal XKB keymap warnings. The test connected, created both synthetic windows and recorded the exact live `/usr/bin/Xvfb` PID/hash, but the listener warning remains an environment caveat.
- This is one synthetic Xvfb schedule, not reliability or efficiency evidence. It does not qualify physical desktop control, MAP01, another domain, WSLc, or universal release during a whole-server/OS stall. It does establish a new scoped timing observation on the PR #9354 caller instrumentation.

## Preserved raw and audit

`stdout.log`, `result.json`, `result.observation.png`, `xvfb.log`, `dependency-install.log`, and `pip-freeze.txt` preserve the first run and its setup. The test was not rerun. `audit.ps1` independently reconstructs event count, effect values, key states, old-cancellation fence, and timing intervals from the retained JSON; all checks pass and the derived intervals match the harness-reported values. `audit_history.md` records an initial numeric-type check that was too strict and its correction; the raw test result was unchanged. `SHA256SUMS` covers packet files except itself.
