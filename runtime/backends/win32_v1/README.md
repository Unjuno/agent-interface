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

Successful executions report `program_emissions` for that invocation. The count is execution-local and excludes earlier backend emissions and terminal/compensating release activity. `Win32ExecutionError` retains the same count before cleanup starts; the runtime session returns it with the failed result and reports `input_dispatched=true` when it is positive. A zero count is preserved as `program_emissions=0` without asserting a pre-input refusal, because cleanup may still have emitted input. This count reports dispatch attempts accepted by the backend, not application delivery or task effect.

The supervised native producer also keeps a shared monotonic lower bound of program input actions accepted by the operating system: `SendInput` events and successful `SetCursorPos` moves. It is a single-writer, four-byte-aligned counter with no process-owned lock, so forced producer retirement cannot strand the recovery reader. If termination interrupts an increment, the prior lower count remains; zero after interruption stays unknown and never becomes a pre-input refusal. A positive lower bound supports `input_dispatched=true`, but does not prove that the target application consumed the event or that the requested task effect occurred. Recovery release/readback remains a separate receipt.

This path is not considered supported merely because it imports or compiles. Promotion requires the frozen native Windows integration block to pass on an actual Windows runner. Secure desktop, elevated/UIPI boundaries, IME behavior, mixed-DPI multi-monitor setups, and privileged applications remain outside v1 unless separately evidenced.

The release ledger treats zero from `GetAsyncKeyState` as unknown, since Windows
also returns zero on API failure. Each tracked key/button remains owned until
its own readback reports the high bit clear; a query or release error for another
obligation does not cause that confirmed-neutral input's UP to be sent again.
Explicit UP with unknown state stops following task operations. A replacement session wrapper
also refuses task input while backend key/button/Unicode custody remains; cleanup
and explicit session recovery remain distinct from task success or replay.
Each terminal `release_all` result also retains one `release_attempts` row per
Unicode, key-encoding, or button UP helper call. The row distinguishes whether
`SendInput` began, its returned count (one is required for helper success), and
an exception. This records only OS API insertion outcome; it does not establish
physical neutral state, application receipt, or task effect. The separate
`verified` field still depends on independent key/button state readback.

Zero may also occur for a healthy up key. Without an independent availability
witness this conservative policy can quarantine the session indefinitely; it does
not establish a physical release-time bound or global input neutrality. The low
bit is unreliable, so its absence is not an availability witness. See the
[Microsoft API contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getasynckeystate)
and [current-main consolidation controls](../../../research/integration/win32_custody_convergence_20261016/README.md).

## Target requirement for new input

Win32 preflight requires a prior `focus` operation or an explicitly bound target before key-down, chord, text, scroll, or pointer-button down. Programs that previously relied on whichever window happened to be foreground must name a target. Explicit UP and `release_all` remain available without a target for recovery. Foreground checks and OS input insertion are not atomic; this rule does not prove application delivery or physical release.
