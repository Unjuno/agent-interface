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
- terminal tracked key/button release verification;
- per-key DOWN/UP transition records that pair `SendInput` acknowledgement times
  with `GetAsyncKeyState` samples before and after each owned key transition.

The returned `execution.input_transitions` records bind the session's admission time,
program ID, and operation index to a stable per-hold identity,
preserve explicit UP and cleanup UP attempts separately, and include a conservative
`os_state_change_window_ns` when before/after OS samples differ. `SendInput`
acknowledgement and `GetAsyncKeyState` do not prove
physical keyboard hardware state or delivery to the target application. An unavailable
per-transition sample is retained as unavailable and does not block the key send;
the existing final neutral-state check remains fail-closed for terminal completion.

Core admission runs before native preflight. Native target/key/text/frame constraints are preflighted before the first physical emission. Stale observation, stale binding, lease expiry, native preflight failures, and unsupported coordinate frames must produce zero task input.

This path is not considered supported merely because it imports or compiles. Promotion requires the frozen native Windows integration block to pass on an actual Windows runner. Secure desktop, elevated/UIPI boundaries, IME behavior, mixed-DPI multi-monitor setups, and privileged applications remain outside v1 unless separately evidenced.
