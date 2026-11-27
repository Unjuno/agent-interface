# Public stdio clock call-path follow-up (2026-11-13)

## Question

Does the public stdio MCP server return a clock sample that the calling process
can bracket in the same Windows monotonic-clock domain, while the call remains
strictly input- and authority-free?

## Method

Added `test_stdio_clock_is_parent_bracketed_and_issues_no_authority` to
`runtime/cli_v1/test_mcp_server.py`. The Windows parent test launches the real
`python -m runtime.cli_v1.mcp_server` stdio entry point with
`mcp.client.stdio`, discovers `interface_clock`, and makes two calls. Each
server timestamp is checked between parent `time.monotonic_ns()` reads. The
test also checks the empty argument schema, stable server instance ID,
nondecreasing samples, `input_dispatched=false`,
`authority_granted=false`, `lease_issued=false`, and an empty isolated receipt
directory. A deliberately invalid display name is configured; the clock-only
path succeeds without opening that display.

## Conditions and result

- Host: Windows 10 build 26300.
- Parent and spawned stdio server: CPython 3.11.9 at
  `C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe`.
- Commands, from the repository root:
  - `python -m unittest -v runtime.cli_v1.test_mcp_server.PublicMCPTests.test_stdio_clock_is_parent_bracketed_and_issues_no_authority runtime.cli_v1.test_mcp_clock`
  - `python -O -m unittest -v runtime.cli_v1.test_mcp_server.PublicMCPTests.test_stdio_clock_is_parent_bracketed_and_issues_no_authority runtime.cli_v1.test_mcp_clock`
- Result: 4/4 tests passed normally and 4/4 under `-O`.
- `git diff --check` passed.

The actual client-to-stdio-server invocation therefore produced two bracketed
samples with one server identity and no authority, lease, input, or result-file
side effect in this tested configuration.

## Scope and next boundary

This is one Windows/Python configuration. Both processes use the same
interpreter and native monotonic implementation. It does not test conversion
between Python 3.11 GetTickCount64 and Python 3.14 QPC, server replacement
between a sample and action, sleep/resume behavior, a lease crossing expiry,
native key-up timing, or task effect. It is not a physical-input experiment or
a 20 ms guarantee.

The source checkout does not contain the previously referenced
`windows_deadline_clock_callpath_20261113/RESULT.md` packet; that historical
preflight/custody result is summarized in `docs/CURRENT_GOAL.md` but could not
be independently rehashed from this checkout during this follow-up. This
report records only the new stdio test and does not claim to replace or
reproduce the missing packet.
