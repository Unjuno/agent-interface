# Win32 foreground-gated blocked-cancel recovery R29

Date: 2026-10-26. Source main: `575ce5665086f2cdfa108bace9ae9a82933aac25`; tree: `a7a57f7c8793e102709eeaec57a249bd8c3c1947`.

## Result

One fresh native Win32 synthetic-fixture trial passed its frozen scoped audit (11/11 checks). A visible fixture (PID 58292, HWND 7932914) was raised through CUA, then passed independent exact PID/HWND foreground checks both before the probe and immediately before public dispatch. One standard-caller call (call `32fe505dee9e42d3ae3309e338b1d160`, operation `1dfbd986516442398b1e76ac73edb62d`) used target generation `853e9167f57c24f8ac4b76f1176ff4d677c60e370a53b4cb9cb044440b16fdb5`.

An injected left-Ctrl down entered the low-level hook and was held when public cancellation began. The cancel response was `pending` after 2.2356 ms (frozen bound: 250 ms); the hook returned 0.7104 ms after that response. Once the harness released the callback gate, the exact action and cancellation receipts became `recovered`, reported release confirmation, and denied replay. Runtime cleanup latency was 15 ms on its monotonic clock and 29.1686 ms on its performance-counter clock. The producer was retired (exit -15).

The fixture event log recorded exactly `R29N7Q4F`. An independent exact-call task verifier returned success with a receipt bound to the call, operation and target generation. The runtime terminal action/cancellation still retain `task_success=null`; the canceled action's own effect status remains unknown. Independent same-generation Win32 observers found Ctrl up 213.139 ms after recorded recovery completion and again 1.835 s after it. The exact fixture exited 0, the hook stopped, and the server closed with no unresolved calls. Three pre-existing GZDoom processes were not targeted and remained alive.

## Boundary

The recorded recovery-completion timestamp is 27.3588 ms after hook return. The packet does not time when the native key state first became neutral inside that interval. Therefore this run shows a fast public cancellation response while the injected Ctrl-down callback was held, followed by finite recovery and neutral readback; it does not prove release completed while the blocked callback remained held.

This is one same-PC synthetic fixture sample, not a guarantee for arbitrary OS/kernel I/O, a reliability estimate, MAP01 completion, or a matched-efficiency result. It uses no WSLc, Docker, provider or model allocation. The prior R28 predispatch failure remains separate and unchanged.

## Evidence custody

The seven-file frozen input manifest and post-trial 49-file manifest both passed hash checks. Raw protocol receipts, fixture logs, observer outputs, images, exact conditions and audit are retained locally at `C:\Users\user\Documents\Codex\2026-10-03\new-chat-2\private-packets\win32_blocked_cancel_foreground_recovery_20261026_r29`; this private packet is not part of this commit.
