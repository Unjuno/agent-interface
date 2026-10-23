# Win32 SendInput low-level-hook delay probe — R01

## Claim and decision rule

Determine whether a native `SendInput` call on this Windows session remains blocked while the installing thread's `WH_KEYBOARD_LL` callback deliberately delays one injected F13 key-down for at most 50 ms. PASS for the narrow hypothesis requires: hook installation and message loop confirmed; exactly one injected F13 down reaches the callback; callback delay is at most 60 ms; the sending call duration overlaps that delay and returns only after callback return; exactly one F13 up is subsequently observed and `GetAsyncKeyState(VK_F13)` is neutral; the hook thread exits and the hook is removed. Any setup, timeout, or cleanup uncertainty is UNKNOWN and no second scientific run is allowed in this packet.

This is not a test of a permanently blocked native call, a hard release deadline, runtime-session recovery, the public MCP caller, task effect, or MAP01. The existing runtime serializes synchronous `SendInput`; the experiment probes one finite OS callback stall only.

## Safety and conditions

- One run, on the user's interactive Windows PC, with an owned F13 injection only. No mouse movement, text entry, target-window changes, registry changes, privilege changes, or external application edits.
- Installs a transient low-level keyboard hook. All events other than the first injected F13 key-down are passed immediately to `CallNextHookEx`; that one callback waits no longer than 50 ms. This hook is desktop-wide, so physical keyboard events could be delayed during that brief callback.
- A `finally` cleanup unhooks and stops the message-loop thread. The runner also attempts one F13 key-up in `finally` if an exception occurs after down injection.
- Clock: Python `time.perf_counter_ns()` (Windows QPC-backed monotonic clock). Raw contains callback entry/exit, SendInput call entry/return, key-state samples, and cleanup outcome.
- Code and protocol are frozen by SHA-256 before the run. Do not rerun this allocation after a result.

## Files

- `probe.py`: self-contained native Win32 probe.
- `conditions.json`: frozen environmental settings and acceptance rule.
- `raw.json`: first-run machine-readable result (created once by the probe).
- `audit.json`: independent post-run check (created once by the auditor).

## Result

**FAIL against the frozen acceptance rule.** The single injected F13 down reached
the hook once. The callback remained active for 64.4284 ms, exceeding the frozen
60 ms maximum despite the 50 ms wait request. `SendInput` returned 0.9093 ms
after callback return; it reported one event. One injected UP was observed,
`GetAsyncKeyState`'s high bit was clear afterward, `UnhookWindowsHookEx`
succeeded, and the hook thread exited. The UP call took 0.3290 ms.

The measured ordering supports the narrow observation that this `SendInput`
call returned after the deliberately delayed low-level callback. The packet is
still FAIL because its predeclared callback-delay bound was exceeded. The 50 ms
wait request is not a hard callback execution bound: scheduler/dispatch overhead
added about 14.43 ms. This does not establish a hard release deadline, behavior
under an indefinitely blocked callback, runtime supervisor recovery, or public
MCP behavior. The outcome is frozen; do not rerun this allocation.

The independent audit in `audit.json` verifies unchanged frozen source hashes,
event counts, timing order, neutral state, and cleanup. `raw.json` contains the
original QPC readings, callback events, API results, and cleanup record. The
probe ran on Windows 10 build 26300 with 64-bit Python 3.11.9. It changed no
registry settings and opened no target application.
