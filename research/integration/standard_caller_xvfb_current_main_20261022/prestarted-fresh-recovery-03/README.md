# R03 independent standard-caller Xvfb repeat

**Run ID:** `AI-XVFB-PRESTARTED-FRESH-RECOVERY-20261022-R03`
**Source:** current main `6b276fcabfa11c060282e0714501a1057e75c0a6`
**Environment:** Ubuntu 24.04 WSL2, private user/mount namespace and private Xvfb `:88`; no WSLc or Docker allocation.

## Outcome

The frozen standard-caller test ran exactly once and passed (`unittest` 1/1, test exit code 0). Xvfb also exited 0. The shell wrapper itself exited 2 after completing cleanup because its CRLF-terminated final `exit 0` was parsed as an invalid numeric argument; that wrapper error is retained in `raw/runner.log` and the test was not rerun. A post-run process check found no Xvfb process.

Measured from cancellation admission: caller response 255.100 ms (within the frozen 300 ms target), supervisor readback 323.415 ms, terminal cancellation receipt 329.723 ms, separate parent-X-client keymap readback 386.460 ms, and delayed-request horizon 8,505.466 ms after cancellation start. Independent keymap observations were all-up at release and at the horizon, with no delayed old `b` press.

A new target XID (`2097154` vs `2097152`), session ID and process-generation digest were distinct. Its synthetic task oracle observed `[0]` before input and `[3]` after input and at the horizon. The oracle passed; the runtime task-success field remained null. The old cancelled operation remained `UNKNOWN`, `late_server_request_possible=true`, `release_confirmed=false`, and replay-denied.

This is the second observed pass of this one Xvfb schedule, not a reliability estimate. The owner was blocked in real `Display.sync()` while the X server remained responsive to the prestarted supervisor. It does not prove release while the whole X server is unavailable, owner-exclusive XTest control, physical GUI/MAP01 success, matched efficiency, or WSLc portability.

## Conditions and preserved first outcomes

The run used the frozen one-second owner-ack withholding, eight-second delayed keypress, pinned existing Python dependency cache, and 45-second outer timeout. No package installation, network download, WSLc command, Docker command, or container/image operation occurred. `conditions.json` and `PLAN.md` were written before the candidate invocation.

Three preflight-script failures are retained: a Windows worktree `.git` pointer was not readable by Linux Git; then CRLF and repeated-space parsing broke the source-manifest check. These were preflight-only failures. The fourth preflight correctly matched all five source hashes and proved the private namespace mount worked. None invoked the candidate. The later candidate wrapper error is retained separately from the passing unittest and Xvfb exit codes; no retry was made.

`raw/SHA256SUMS.txt` binds every raw output and preflight record. `audit.json` and `verify_r03.py` independently check source hashes, timing, generation identity, oracle and old-fence invariants.
