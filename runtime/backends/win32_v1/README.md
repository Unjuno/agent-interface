# Win32 runtime backend v1

Product-integration candidate for Issue #622. It implements the promoted `runtime/core_v1` backend boundary with Python stdlib `ctypes` over Win32 APIs.

The backend is intentionally narrow:
- explicit registered HWND targets;
- `screen_physical_px` and `window_client` coordinates;
- keyboard/key-state/chords and Unicode `SendInput` text;
- pointer/buttons/wheel;
- client/screen GDI capture;
- foreground focus verification;
- monotonic wait/feedback;
- terminal tracked key/button release verification.

Core admission runs before native preflight. Native target/key/text/frame constraints are preflighted before the first physical emission. Stale observation, stale binding, lease expiry, native preflight failures, and unsupported coordinate frames must produce zero task input.

This path is not considered supported merely because it imports or compiles. Promotion requires the frozen native Windows integration block to pass on an actual Windows runner. Secure desktop, elevated/UIPI boundaries, IME behavior, mixed-DPI multi-monitor setups, and privileged applications remain outside v1 unless separately evidenced.

The release ledger treats zero from `GetAsyncKeyState` as unknown, since Windows
also returns zero on API failure. Tracked keys/buttons remain owned and release
is unverified until a nonzero sample reports the high bit clear. Explicit UP
with unknown state stops following task operations. A replacement session wrapper
also refuses task input while backend key/button/Unicode custody remains; cleanup
and explicit session recovery remain distinct from task success or replay.

Zero may also occur for a healthy up key. Without an independent availability
witness this conservative policy can quarantine the session indefinitely; it does
not establish a physical release-time bound or global input neutrality. The low
bit is unreliable, so its absence is not an availability witness. See the
[Microsoft API contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getasynckeystate)
and [current-main consolidation controls](../../../research/integration/win32_custody_convergence_20261016/README.md).
