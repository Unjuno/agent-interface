# Standard-caller blocked-X11 release probe (2026-10-19)

## Question

Can the supported guarded-X11 MCP caller return within a finite bound when its
owned X11 request is blocked waiting for a server reply, while retaining an
`UNKNOWN` release/task outcome and preventing replay? The synthetic target must
independently observe the key event and task effect; the parent XRes, keymap,
and release observers use a direct connection.

## Attempts and retained outcomes

| Packet | Allocation | First outcome | What it establishes |
|---|---|---|---|
| [A02](../standard_caller_blocked_x11_release_a02_20261019/) | `4cc5f51c7d95d3def10b684b4613d08a0bcd9d13bd1621dd9a9bfdea43d58e36` | `STOP_FAIL_SOURCE_MOUNT_INCOMPLETE`; probe main was never entered because the read-only `/repo` mount omitted `runtime/`. WSLc exit 1. | Runner packaging failure only. This is immutable and must not be rerun. |
| [A03](../standard_caller_blocked_x11_release_a03_20261019/) | `fb137ba1d99ee8f707d07e41379197759ff9daed51491064a504abb005b5cf5d` | `FAIL_FIRST_OUTCOME_RETAINED`; one healthy control passed, then blocked trial 01 timed out waiting for `owner_reply_held.json`. WSLc exit 1. | Healthy standard-caller path works once under this synthetic setup. The blocked-path predicate was not reached/confirmed; this is not evidence of bounded cancellation or release. Do not rerun A03. |
| [CI Xvfb setup attempt](../standard_mcp_xvfb_blocked_release_r01_20261019/) | PR head `6c69f595c0e1d61b0bad0568fde3d05c5d3e841b`, run [39226642774](https://github.com/Unjuno/agent-interface/actions/runs/39226642774) | `FAIL_TEST_CONFIGURATION`; the standard caller returned an observation with process generation but no window generation because this test omitted `guarded_window_lifecycle=True`. Assertion stopped before input dispatch. | No blocked-I/O, release, task-effect, or recovery result. Preserve the first raw packet unchanged; the corrected configuration is being tested at a new source revision. |
| [Corrected-configuration Xvfb attempt](../standard_mcp_xvfb_blocked_release_r01_20261019/run-39227740722/) | PR head `a0f69e5157190ed5097b249be7e10f5d5da82845`, run [39227740722](https://github.com/Unjuno/agent-interface/actions/runs/39227740722) | `FAIL_TEST_HARNESS_SIGNATURE`; observation returned process and window generations, then the test wrapper raised `TypeError` because it did not accept the caller's `root=` keyword. The injected press and delayed request were not sent. | This run reaches the expected generation and observation path but does not test blocked I/O or release. Raw JSON and image are retained. The wrapper signature is being corrected at a new source revision. |
| [Marker-directory Xvfb attempt](../standard_mcp_xvfb_blocked_release_r01_20261019/run-39228136905/) | PR head `7d7360f22cdd33bb15e23aa094e7384d359a9a56`, run [39228136905](https://github.com/Unjuno/agent-interface/actions/runs/39228136905) | `FAIL_MARKER_DIRECTORY_MISMATCH`; the test waited for markers under the temporary root, while the owner factory receives the MCP output directory (`root/mcp`) and writes them there. The caller returned `pending`; cleanup reports a timed-out owner process and release `UNKNOWN`, but the intended markers and independent effect/readback were not captured. | Treat input delivery and blocked-sync entry as unverified. Preserve raw and image; align the waiter with the factory's directory before another fresh-source run. |
| Clock-name Xvfb attempt | PR head `3984c9341712c043ae45912ba2af3d332c16f555`, run [39228685920](https://github.com/Unjuno/agent-interface/actions/runs/39228685920) | `FAIL_TEST_HARNESS_NAME_SHADOW`; the marker directory was correct, but the wrapper parameter `time` shadows the imported module at `time.monotonic_ns()` before the delayed-request marker is written. | The report records pending input and cleanup `UNKNOWN`; it does not contain the wrapper exception or prove blocked-sync entry. Preserve the raw; use a non-shadowed monotonic clock function and rerun from a fresh source revision. |

A03's retained blocked report shows the synthetic app saw event type 19
(`MapNotify`), the input call first returned `pending`, and the eventual result
was `refused` with `process identity unavailable; explicit review required`,
`input_dispatched=false`, and no guard checks. Final cleanup was
`cleanup_failed`/`UNKNOWN`; the report's `finally_cancel` was `not_active`, with
`release_confirmed=false`. The owner connection reached the in-process proxy
(`owner_peer.json`, peer PID 24), and `input_started` exists, but no
`owner_reply_held.json` exists. The task KeyPress and effect were never
independently observed.

The likely cause is a circular gate in the frozen probe: after `input_started`,
the proxy withholds every type-1 reply from any connection whose peer PID is the
owned process, waiting up to 1.5 seconds for the app's KeyPress marker. The
standard caller must first revalidate target process identity before dispatching
that KeyPress; that read-only query uses a separate X connection from the same
owner process and can therefore be caught by the broad reply predicate. The
retained caller result is consistent with that pre-press query timing out and
the target-query worker retiring. This is a source-and-result-supported
diagnosis, not a proven reply-level trace: A03 did not record the held reply
sequence or per-connection query sequence. Do not infer that the intended
input-reply gate was reached or that the task effect occurred.

A03 stopped after the first blocked failure as preregistered. Its exact frozen
conditions, source hashes, command, container identity, all raw output, and
empty post-run-container list are preserved under its `raw/` directory.

The staged dependency bundle is pinned by SHA-256
`0e810d23a4ee0898fbec3fdd4add6381f5952785160d4cb90936692b7f123106` and was
mounted read-only. The A03 container had no network, used the cached image by
immutable ID, mounted the whole repository read-only, and wrote output only to
its unique external directory before raw was copied here.

## Next finite step

The test now waits in the owner output directory and records that directory in
the report. The remaining wrapper defect is the `time` parameter shadowing the
imported module used for the marker timestamp. The wrapper now calls a separately
imported `_monotonic_ns`; rerun from a fresh source revision and preserve the
raw JSON and image or exact failure. Audit input, blocked-sync entry,
cancellation, independent release readback, late-request horizon, and bounded
terminal-result checkpoints. Treat either delayed-`b` outcome as a result, but
retain `release_confirmed=false`, cleanup `UNKNOWN`, task success `null`, and
replay disabled. This is one private-Xvfb synthetic target; it does not replace
the separate real-X11 proxy framing/order question or qualify physical release.

## Evidence boundary

The one healthy control is synthetic Xvfb composition evidence only. Neither
attempt proves blocked server-I/O cancellation, independent post-cancel key-up,
physical/XWayland release, real-application success, MAP01, bounded recovery,
or matched efficiency. No runtime production files changed in these attempts.
