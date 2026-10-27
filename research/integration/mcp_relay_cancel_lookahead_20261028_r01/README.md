# MCP relay cancellation lookahead regression

Date: 2026-10-28 (Asia/Tokyo)
Repository revision: `0088c96d17df8ef31c25ad1cba5f2ac883f72f28`

## Finding

The Native MCP CI artifact for PR #9785 showed `test_two_queued_ordinary_requests_delay_cancel_until_stdout_resumes` failing because `queued-two` was dispatched before a cancellation request that raced with the bounded input reader. The test fixed an ordering that the documented contract does not promise: after stdout resumes, a cancellation already returned by the one-line lookahead may overtake the deferred ordinary request; if the lookahead has not returned, FIFO may dispatch that ordinary request first. The test still requires both queued ordinary requests to remain undispatched while stdout is blocked, and cancellation dispatch to occur only after stdout resumes.

The test now accepts both post-resume orders while preserving those backpressure and delayed-cancellation assertions. Runtime behavior is unchanged.

## Reproduction conditions and results

WSL Ubuntu, CPython 3.12.3, `mcp==1.30.0`. Tests used a venv outside the repository and a detached pre-fix worktree at the same repository revision. The MCP relay module test was run after the change with only its legacy parity test excluded because that dependency module is omitted from this sparse checkout.

- Before: 1 failure in 20 executions of the targeted test.
- After: 0 failures in 20 executions of the targeted test.
- After: 22/22 available `runtime.cli_v1.test_mcp_relay` tests passed.
- CI-equivalent full native runner is not accepted as a pass: this local sparse checkout omits protocol modules and `runtime.backends.win32_v1`; `native-full-result.json` records its fail status. The source-gate CI artifact had 692 protocol tests with this one test failure; the separate harness and Win32 suites passed in that run.

Raw repeated-test logs, relay suite output and native-run summary are retained here. SHA-256 values are in `SHA256SUMS`.

## Scope

Offline relay contract tests only. No MCP server, GUI, live input, Docker Engine, WSLc, MAP01, or provider calls were executed. This changes test scheduling expectations, not cancellation semantics, input release, or server-side queue drainage.