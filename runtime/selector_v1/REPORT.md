# Promoted backend selector v1

Task `RUNTIME-BACKEND-SELECTOR-V1-20260917-001`, Issue #639.  
Immutable integration base `537bad4144f35bc0faf57202ba42fefd43ae6933`.

Decision: **`PASS_PROMOTED_BACKEND_SELECTOR_V1`**.

The selector adds no execution capability. It maps explicit host/session evidence
to the already-promoted native backend identifiers and keeps
`side_effect_authority=false`; actual authority remains a backend-manifest and
core-admission decision.

Frozen selection floor:

- Linux + `DISPLAY` -> `x11-v1`, explicit X11 window IDs;
- Windows -> `win32-v1`, explicit HWNDs;
- macOS -> `quartz-v1`, explicit PIDs;
- Wayland-only Linux -> `WAYLAND_BACKEND_NOT_PROMOTED`;
- Linux without an interactive display -> `NO_INTERACTIVE_DISPLAY`;
- unknown platforms -> `UNSUPPORTED_PLATFORM`.

`open_session()` intentionally has no foreign-platform override. Foreign plans
may be inspected in deterministic tests, but a process cannot instantiate a
foreign backend and turn that into false support evidence. Target registries
must be nonempty mappings from bounded names to positive integer native IDs.
Imports remain lazy so platform-specific dependencies are loaded only for the
actual selected host.

GitHub Actions run `35127817571` passes on ubuntu-latest, windows-latest and
macos-latest. Every job passes compile plus **10/10 selector contract tests**.
Existing backend-native effect CIs remain the authority for X11, Win32 and
Quartz execution semantics.

This result does not promote Wayland, discover targets, or widen any backend's
support envelope.
