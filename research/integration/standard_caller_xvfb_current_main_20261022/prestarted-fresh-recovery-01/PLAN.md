# Prestarted supervisor + fresh-session recovery, standard caller

**Run ID:** `AI-XVFB-PRESTARTED-FRESH-RECOVERY-20261022-R01`
**Source:** current-main checkout `cdc8bd6b65bf976137db645c2be31e20090f7d67`
**Status:** frozen before execution; one run only

## Question

With the standard MCP caller's prestarted cancellation supervisor enabled, does the held-ack blocked-owner scenario return its cancellation response within the 300 ms research target, and can a distinct fresh session on the same private X server complete its synthetic task while the old session remains truthfully `UNKNOWN` and replay-denied through an 8 s delayed-request horizon?

## Frozen method

Run the existing `StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb` once against the exact current-main source. Use Ubuntu 24.04 WSL2, CPython 3.12.3, a private Xvfb at `:88`, and the workflow's pinned top-level dependencies (`python-xlib==0.33`, `Pillow==10.2.0`, `numpy==1.26.4`, `mcp==1.30.0`) installed only under `/tmp`. Set `AGENT_INTERFACE_MCP_XVFB_TEST=1`, `AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=1`, `AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS=1`, and `AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=1.0`. Pass the live Xvfb PID and `raw/result.json` through the test's documented environment variables. Preserve exact stdout, stderr, exit code, Xvfb log, report, package versions, and hashes under `raw/`.

The existing test's assertion bound is 3000 ms. Independently classify response latency against the stricter 300 ms research target; a passing unittest alone does not satisfy that target. The synthetic fresh-task oracle expects property `[0]` before its input and `[3]` after input and at the horizon. Retain any old delayed `b` event as evidence rather than assuming queue cancellation.

## Decision rule

- **PASS, scoped:** unittest passes; cancellation caller response is at most 300 ms; independent release readback is all-up; fresh target/session/process generation is distinct; the new task oracle passes at input and horizon with no old delayed press after fresh-session start; the old cancellation remains `cleanup_status=UNKNOWN`, `late_server_request_possible=true`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`; final cleanup reports all keys up and all processes exit.
- **HOLD/FAIL:** preserve the first result and classify the specific failed predicate. Do not rerun this run ID or tune conditions after observing the outcome.

## Limits and stop boundary

This is one synthetic private-Xvfb standard-caller trial. It does not prove a universal server-wide release bound, exclusive ownership of global XTest key state, physical desktop control, Windows/WSLc portability, MAP01 success, reliability, or matched efficiency. It does not authorize WSLc or Docker; no WSLc allocation is used. Supervisor remains default-off. Runtime `task_success` must remain null for the old operation.
