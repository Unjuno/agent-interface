# Standard caller under a stopped private X server — r01

This packet preserves the first retained result from the Linux private-Xvfb server-stop regression. It is a scoped integration result and a counterexample to assuming that a bounded cancel response guarantees a released key.

## Source and run

- Merged test change: [PR #9220](https://github.com/Unjuno/agent-interface/pull/9220), main merge commit `de852bf3b65ad5b8debac3b7e0138bcf843e7313`.
- Exact test source at the producing head `4262d979a451266dae79e595aa68dc7ef400331c`: `runtime/cli_v1/test_mcp_xvfb_server_stop_integration.py` (Git blob `c44b82464bf78137d45a344731d5568158239235`).
- Exact workflow at that head: `.github/workflows/runtime-x11-v1.yml` (Git blob `7a55cdd03b0a21f595860d8ba9166b4863008106`).
- Run: [GitHub Actions 39373461786](https://github.com/Unjuno/agent-interface/actions/runs/39373461786), job `x11-integration`, completed successfully at 2026-10-20 05:12:24 UTC. The run used the workflow-owned Linux Xvfb `:88`; it did not use WSLc, Docker, a live provider, or MAP01.
- Raw report: [`RESULT.json`](RESULT.json). It was downloaded from the named run artifact `standard-mcp-xvfb-server-stop` without editing. SHA-256: `c9ebc6cdaa9b1ee57d61e7b8429aa2eda4c8263bfe5fb9a46ac492ad8362baa9`.

## Conditions and result

The standard owned MCP caller held key `a` after producing synthetic effect `[1]`. The fixture verified the identity of its workflow-owned Xvfb process, sent `SIGSTOP` while `Display.sync()` was blocked, and then canceled. The declared cancellation-response bound was 3.0 seconds, the delayed-request time field was 8,000 ms, and the exact Xvfb process was resumed with `SIGCONT` (with a 4-second safety resume).

Cancellation returned before server resume in 0.409214 seconds. The owner process retirement receipt was true, but the XRes client-disconnect observation was `UNKNOWN` after a 152.483 ms supervision timeout. The caller therefore correctly recorded `owner_release_attempt=not_attempted` with reason `owner_disconnect_not_confirmed`; runtime release remained `UNKNOWN`, cleanup `UNKNOWN`, `task_success=null`, and replay disabled.

After resume, a separate parent X client still observed `a` down both on the immediate release readback and at the 8.5-second horizon. The report also says a release event was seen while the keymap still reported `a` down. The declared synthetic task oracle therefore returned `fail` (`horizon_readback_all_up=false`). The test's final fixture cleanup later read both keys up; that teardown action does not upgrade the caller's release receipt or task outcome. The raw also contains a contradictory terminal snapshot (`owner_process.alive=true`, `retired=false`) beside the cancel receipt (`owner_process_retired=true`, exit `-15`). Preserve and investigate both mismatches rather than selecting one field as authoritative.

## Interpretation and next discriminator

The regression passed its safety assertions: cancellation returned within this fixture's bound, the caller did not claim release when disconnect was unconfirmed, and replay stayed disabled. The observed application task failed because key `a` remained down after server resume. This is not a release pass, a physical-desktop result, an application-independent MAP01 score, or a general server-outage guarantee.

Keep Issue #17 open. The next finite source/test check is to reconcile the cancel-retirement receipt with the terminal owner-liveness snapshot and identify whether an existing caller-owned cleanup path can establish key-up after X-server resume without trusting the test fixture's direct key release. Do not rerun or relabel this retained run; any new schedule needs a separate result identity and must preserve this failure.

## Integrity

`SHA256SUMS` covers the raw result and this README. The test and workflow blob IDs above identify the exact producer source; the original Actions artifact remains the upstream copy of the raw report.
