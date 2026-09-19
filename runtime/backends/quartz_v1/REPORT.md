# Native Quartz runtime backend v1

Task `RUNTIME-QUARTZ-BACKEND-V1-20260917-001`, Issue #631.  
Immutable integration base `1293f827ec758aaa380201fc718bc6e42151459b`.  
Source-first freeze `91d0c3128f2af0dfe735664d0ebc33e1922e9e10`.

Decision: **`PASS_NATIVE_QUARTZ_V1_SCOPED`**.

## Integrated boundary

`QuartzRuntimeSession` composes the unchanged promoted `runtime/core_v1`
admission contract with a Python-stdlib `ctypes` backend over
ApplicationServices/CoreGraphics/CoreFoundation.

The backend uses explicit target PIDs, reports actual Accessibility and Screen
Recording permission state in its capability manifest, and exposes only
`screen_physical_px` rather than inventing window-client geometry. The
correctness-floor capabilities are AX frontmost focus, Quartz keyboard/Unicode
text, pointer/buttons, wheel scroll, display geometry/capture, monotonic wait,
and tracked terminal release verification.

## Source-first / construction boundary

Before native execution, exact backend/session/fixture/test source was published
and frozen by Git blob identity. Container construction only compiled source and
ran **2/2** pure helper tests for UTF-16/key mapping and fail-closed permission
manifests. Native measured executions before the freeze were zero.

## Frozen first native outcome

GitHub Actions run `35127339288`, head
`096ae8ffd485e6c1b5e09e6e13faac2cbad2e454`, ran once on macOS 26.6.2
(`25G83`, `macos-26-arm64`, CPython 3.12.10):

- pure helpers: **2/2 PASS**;
- native integration: **9/9 PASS**;
- Accessibility permission: **granted**;
- Screen Recording permission: **granted**.

The primary positive path launched the system `/usr/bin/osascript` native
`display dialog` fixture. The backend targeted that process by PID, made it
frontmost through Accessibility, injected Unicode text `office`, captured a
200x120 screen region through CoreGraphics, pressed Enter, and ended with
verified empty tracked key/button state. The independent fixture wrapper—not the
backend—parsed the dialog result and retained the exact returned text.

A separate pointer case moved the physical cursor to `(40,40)` and read the
current Quartz pointer location back within the frozen tolerance.

Zero-event/effect controls passed for stale observation, stale binding, expired
lease, unknown/stale target PID, explicit-surrogate Unicode rejection, and
unsupported `screen_logical` coordinate frame. The pure permission control also
verifies that denied Accessibility/Screen Recording states become
`permission_required`, never implicit support.

No same-identity native rerun occurred before the first result.

## Scope limit

This is scoped native execution evidence on one hosted macOS arm64 runner, not a
general macOS population guarantee. TCC persistence for signed/notarized apps,
sandboxing, secure input, IME composition, multiple displays/Spaces, privileged
applications and natural focus contention remain outside v1 unless separately
evidenced. Explicit PID targeting is the correctness floor; accessibility-based
discovery may be layered later without changing the common semantic contract.

The frozen 2026-09-17 Research Preview RC remains separate and unchanged by
this post-preview backend promotion.
