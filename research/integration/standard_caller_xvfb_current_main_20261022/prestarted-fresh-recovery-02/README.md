# Standard-caller prestarted cancellation and fresh-session recovery

**Run ID:** `AI-XVFB-PRESTARTED-FRESH-RECOVERY-20261022-R02`
**Result:** unittest PASS; scoped research PASS for the 300 ms caller-response target and the synthetic same-server fresh-session oracle.
**Source:** `cdc8bd6b65bf976137db645c2be31e20090f7d67` (`origin/main` matched).
**Platform:** Ubuntu 24.04.3 / CPython 3.12.3 / Xvfb `2:21.1.12-1ubuntu1.8`, SHA-256 `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`.
**Isolation:** native Ubuntu WSL2; private unprivileged user+mount namespace; a temporary mode-1777 tmpfs hides the shared WSLg socket directory; Xvfb TCP listening disabled. No WSLc or Docker allocation was used.

## Observed result

The exact standard-caller test passed once (`exit-code.txt=0`); the Xvfb process exited 0. The test's own cancellation assertion allows 3000 ms, so its unittest PASS alone would be too weak. The measured public-caller response returned `pending`/`UNKNOWN` 252.924 ms after cancellation admission, within the independent 300 ms research target. The supervisor's release request and its own X11 readback completed at 324.791 ms after admission; an independent parent X client read both `a` and `b` up at 379.339 ms. The cancellation operation reached its retained terminal record at 331.456 ms. The owner acknowledgement was withheld for 1.0 s, but its owner process was retired and a prestarted supervisor disconnected its X client and issued the release.

The old operation correctly remains `cleanup_status=UNKNOWN`, `late_server_request_possible=true`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. The original action later reports `runtime_failed` with `EOFError()` after owner retirement; this did not become a runtime task-success claim.

A new public MCP session on the same X server used a different target XID (`2097154`; old target `2097152`), session ID, and process-generation digest (`2828d997…d9075a`; old `5b1c41d1…22641fa`). Its independent synthetic task oracle saw `[0]` before input and `[3]` after input and at the horizon. All new-session keys were up, no delayed old `b` press was observed after the new session started, and the old UNKNOWN fence was unchanged. The 8.501 s delayed-request horizon also found both keys up and no delayed `b` press. The separate old-session synthetic-task oracle passed its scoped `[1]`-effect definition.

The result JSON preserves the complete operation receipt, timing, source and Xvfb provenance, generation bindings, independent keymap observations, task-oracle checks, terminal state, and final cleanup. The test also emitted `result.observation.png`; it is preserved even though it was not in the original expected-output list. `conditions.json` and `PLAN.md` froze the invocation and decision rule before the candidate test. `raw/SHA256SUMS.txt` binds all raw files; `raw/runtime-manifest.sha256` binds the relevant current-main source files.

## Limits

This is one private-Xvfb trial with the owner blocked in a real Xlib `Display.sync()` wait while the X server remains able to serve a separate supervisor connection. It demonstrates a bounded caller response and scoped release/recovery under that schedule; it does not show release while the whole X server is unavailable, prove owner-exclusive control of global XTest key state, establish an unbounded delayed-request drain, or prove physical desktop/MAP01 success. One trial does not qualify reliability or matched efficiency. Runtime task success remains null and replay remains denied for the cancelled action. The earlier [R01 preflight hold](../prestarted-fresh-recovery-01/STATUS.md) is preserved separately; its candidate test was never invoked.
