# Public stdio and mixed-runtime clock follow-up (2026-11-13)

## Public stdio call-path regression

Added `test_stdio_clock_is_parent_bracketed_and_issues_no_authority` to
`runtime/cli_v1/test_mcp_server.py`. A Windows parent launches the real
`python -m runtime.cli_v1.mcp_server` stdio entry point, discovers
`interface_clock`, and makes two calls. Each server sample is bracketed by
parent `time.monotonic_ns()` reads. The test verifies the empty argument
schema, stable server instance ID, nondecreasing samples,
`input_dispatched=false`, `authority_granted=false`, `lease_issued=false`, and
an empty isolated receipt directory. A deliberately invalid display name is
configured; the clock path succeeds without opening the display.

On Windows 10 build 26300 / CPython 3.11.9, the stdio integration case plus
the three direct clock tests passed 4/4 normally and 4/4 under `-O`.

## Mixed-runtime clock-coordinate probe

The real stdio probe was then run in two configurations. Each made eight
clock-only calls to a spawned MCP server, with the client taking local
`time.monotonic_ns()` readings immediately before and after every call.

| Client | Server | Client clock | Server clock | Server readings inside client brackets |
|---|---|---|---|---:|
| CPython 3.11.9 | CPython 3.13.14 | GetTickCount64, 15.625 ms resolution | QueryPerformanceCounter, 100 ns resolution | 0/8 |
| CPython 3.13.14 | CPython 3.13.14 | QueryPerformanceCounter, 100 ns resolution | QueryPerformanceCounter, 100 ns resolution | 8/8 |

In the mixed run, the server sample exceeded the client's post-call timestamp
by 20.745–33.695 ms; the client's before/after bracket widths were 0–15 ms.
The same-runtime control had bracket widths of 1.296–2.103 ms, with every
server sample inside. Both runs retained one server instance ID, reported no
input/authority/lease, and left the receipt directory empty. Exact samples,
clock metadata and interpreter versions are retained in `run-01/` and
`run-02/`; their SHA-256 values are recorded below.

This demonstrates that parent-side latency measurements cannot safely mix
these two runtime clocks as if they were one coordinate. It does **not** show
that an expiry authored as `server_sample + duration` is rejected: such a
deadline remains in the server's own coordinate and was not submitted to an
action endpoint here. The observed offset also cannot be separated into clock
epoch/quantization versus transport timing from these eight short samples. For
QPC timing experiments, use the same interpreter for caller, server and
helpers, as the runtime documentation already requires.

## Conditions and reproduction

- Host: Windows 10 build 26300.
- Parent/server: CPython 3.11.9 / CPython 3.13.14 for `run-01`; both
  CPython 3.13.14 for `run-02`.
- Runner: `probe.py`, from repository root, with `--server-python` set to the
  selected interpreter executable and `--output` set to a fresh run folder.
- The target map contains only `{"fixture":123}`. The server is given an
  invalid display name as a negative control. No display, target application,
  backend input, authority, lease, or dispatch is opened.
- Each run uses one server process and eight `interface_clock` calls.

Raw file hashes:

- `run-01/mixed-clock-samples.json`: SHA-256
  `c5d08d44a5907aacc70efb05a5c440af88a32df63644d02a96a16e8f554cf248`
- `run-02/mixed-clock-samples.json`: SHA-256
  `55ac4267e0d34796e93678f121c88f7e72d6038ceeeae48d95c6ecac4b0d6a96`

## Limits and missing historical packet

This does not establish action-endpoint acceptance, deadline expiry behavior,
native key-up timing, independent task effect, reliability, or a real-time
bound. The source checkout also lacks the earlier referenced
`windows_deadline_clock_callpath_20261113/RESULT.md` packet. Its historical
preflight/custody result is summarized in `docs/CURRENT_GOAL.md` but could not
be independently rehashed here; this report does not reproduce or replace it.
