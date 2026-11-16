# Win32 prestarted producer candidate (2026-11-17)

This candidate implements the prewarmed one-use producer seam described in
[`win32_prestarted_producer_boundary_20261117.md`](win32_prestarted_producer_boundary_20261117.md).
It is based on main `5cada635a25e0d220500221f485211ea52eca996`.

## Implemented path

- The native supervised Win32 route now creates one idle one-use producer at
  server initialization, before operation admission. The child sends a ready
  receipt and waits without creating a backend or sending input.
- Each operation transfers its immutable program and identities over a private
  pipe. The child returns a SHA-256-bound prepared receipt. The existing owner
  then reads current target generation, records the exact process identity in
  custody, and opens the authorization gate. A mismatched authorization exits
  with zero operation receipts.
- After worker retirement, a replacement is started in a background thread.
  The next dispatch checks readiness before owner admission and refuses before
  admission if no ready worker can be confirmed.
- Existing per-operation counters are preallocated with the worker. The
  ordinary unstarted producer factory path remains supported for injected
  callers and fixtures.
- Server close retires the idle worker. This does not change release, effect,
  uncertainty, replay, or task-success semantics.

## Verification

- `git diff --check` and `py_compile` passed.
- Four focused new cases passed normally and under `-O` on the final candidate:
  exact live-handle use
  without a second start; pre-admission refusal when no worker is ready; real
  spawned-worker ready/ack with mismatched authorization refusal and zero
  actions; native factory ready, retire, asynchronous replenish, and close.
- On the final candidate, full `runtime.cli_v1.test_owned_win32_session`,
  `test_mcp_supervised_win32`, and `test_win32_standard_producer` suites passed
  123/123 normally and 123/123 under `-O`. Earlier full runs intermittently
  observed `recovered` in the existing three-second stdio expiry test where it
  expected `unknown`; a standalone rerun passed. The test depends on timing
  across the public client/server boundary, so the earlier failures remain part
  of the run history and are not hidden by the final passing run.
- The first GitHub Actions run for PR #10350 found an additional integration
  regression: `close_owner()` referenced the Win32 producer-factory local in
  non-Win32 X11 server modes where that local had never been assigned. The
  candidate now initializes the optional factory to `None` before backend
  selection. After this fix, the existing X11 `test_stable_selected_worker_route`
  and queued-expiry transport cancellation case passed normally; both passed
  under `-O` as well. On fixed head `9ba0135d3abc2547df374bddf4f1a77e592856e3`,
  all 18 GitHub check runs completed successfully, including Windows, macOS,
  X11 integration, native Win32, native MCP, replay gate, and evidence checks.
  A subsequent local rerun of those two transport tests passed 2/2 normally and
  2/2 under `-O`; `git diff --check` also passed.

## Limits

No native MAP01 input, delayed-input horizon, HUD effect, or task-success
receipt was run through this candidate. No end-to-end elapsed-time or resource
comparison was measured. This changes where worker startup occurs; it does not
prove that total cold lifecycle latency or repeated-task efficiency improves.
The #57 integrated comparison and live task-effect gate remain open. Do not
promote this candidate as a live-control pass.
