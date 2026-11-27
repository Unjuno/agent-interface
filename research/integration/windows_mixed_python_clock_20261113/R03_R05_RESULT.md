# Public MCP deadline-clock qualification R03–R05 (2026-11-13)

## Result

Three new Windows stdio MCP runs show that `interface_clock` timestamps are not
comparable with a caller's `time.monotonic_ns()` when those processes use
different Windows Python clock implementations. In each mixed-runtime direction,
all 8 server samples fell outside the caller's live before/after bracket. The
same-runtime QPC control placed all 8 samples inside the bracket. All 24 calls
were read-only: one server instance per run, no backend opened, no authority or
lease issued, no input dispatched, and no receipt files created.

| Run | Client clock | Server clock | Server timestamp minus caller's post-call time | Inside brackets |
|---|---|---|---:|---:|
| R03 | Python 3.11.9 / GetTickCount64 | Python 3.13.14 / QPC | +22.459 to +35.968 ms | 0/8 |
| R04 control | Python 3.14.2 / QPC | Python 3.14.2 / QPC | −0.904 to −0.354 ms | 8/8 |
| R05 | Python 3.13.14 / QPC | Python 3.11.9 / GetTickCount64 | −36.096 to −22.268 ms | 0/8 |

The mirrored offset means a caller-authored absolute deadline can be early or
late in the server's coordinate if it is based on the caller's own clock. This
run did not submit any deadline to `interface_dispatch`; it therefore does not
measure action-endpoint acceptance or input effects. The supported usage remains
to author the deadline from a fresh `interface_clock` sample on the live server
connection, while preserving that server identity.

## D05/D06/R142 connection

The current Windows CPython 3.11.9 runtime reports monotonic
`GetTickCount64()` at 15.625 ms resolution while `perf_counter` uses QPC at
100 ns. A new no-input diagnostic ran the actual 2 ms sleep/recheck pattern for
20 independent 50 ms monotonic deadlines under Python 3.11.9 and 3.13.14.
Python 3.11 overshoot was 0.101–12.740 ms (median 12.613 ms); Python 3.13/QPC
overshoot was 0.086–0.388 ms (median 0.180 ms). This is consistent with D05's
clock-quantization diagnosis and D06's no-input QPC loop, while making no
claim about cancellation, SendInput, release, target response, or a 20 ms bound.

R142 remains a failed native MAP01 boundary: 41.941 ms against its unchanged
20 ms gate, with W observed down after expiry and first up 31 ms later. Its
packet does not pin the actual lease-clock implementation and does not record
the exact `SendInput` entry/return timestamp. The new data identifies mixed
clock coordinates and coarse polling as real contributors to control for; it
does not isolate R142's cause. Keep its first outcome unchanged.

## Conditions and custody

- Source commit: `853c37ba9ada99c68352c108a937623f8e059856`.
- Public path: real spawned `runtime.cli_v1.mcp_server` stdio process and
  `interface_clock`; invalid display configured as a negative control.
- R03: Python 3.11.9 client, Python 3.13.14 server; 8 calls.
- R04: Python 3.14.2 client/server; 8 calls.
- R05: Python 3.13.14 client, Python 3.11.9 server; 8 calls.
- A separate raw loop probe retained 20 × 50 ms deadlines per interpreter with
  2 ms monotonic polling and QPC timing.
- All inputs, leases, target applications, and GUI backends were absent.
- Raw outputs, exact conditions, probe source, hashes, and setup-attempt notes
  are in the task-local packet at
  `private-packets/windows_mixed_python_clock_20261113_r03_r04/`.

The historical R142 and DCLK reports remain separate evidence. These clock-only
runs do not establish a physical release, finite recovery, application effect,
MAP01 success, reliability, or efficiency. A fresh live attempt should use one
qualified QPC interpreter for caller, server, and helpers, record the clock
metadata in its frozen conditions, and capture separate cleanup-request and
exact release-call entry/return timestamps before preserving its unchanged
release and task-effect gates.
