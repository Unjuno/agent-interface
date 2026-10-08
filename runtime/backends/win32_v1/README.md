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

The release ledger reads the high bit from `GetAsyncKeyState`. Windows also returns zero when that call fails, so a zero cannot distinguish an observed-up key from an unavailable state read; the value is also only a point-in-time snapshot. A `verified` release therefore means that no high bit was observed in the supported desktop context, not unconditional proof of OS-level neutrality.
