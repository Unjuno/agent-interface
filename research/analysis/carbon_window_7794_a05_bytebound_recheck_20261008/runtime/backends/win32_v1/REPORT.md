# Native Win32 runtime backend v1

Task `RUNTIME-WIN32-BACKEND-V1-20260917-001`, Issue #622.  
Immutable integration base `25dce289aad528b8d1d7d79f910fe4c1c9d49ec4`.  
Source-first freeze `84cd9abfbfb3fabc7e2cfa579fe15cea55b6fdd9`.

Decision: **`PASS_NATIVE_WIN32_V1_SCOPED`**.

## What is integrated

`Win32RuntimeSession` composes the unchanged promoted `runtime/core_v1`
admission contract with a stdlib `ctypes` Win32 backend. Core freshness,
binding, lease and capability checks run first; a whole-program native preflight
then verifies HWND targets, key mapping, text encoding, coordinate frames and
capture bounds before the first physical emission.

The backend exposes the office-floor capabilities for explicit registered HWND
targets using `user32`/`gdi32`: foreground focus, client/screen geometry,
keyboard and Unicode `SendInput` text, pointer/buttons, wheel scroll, client or
screen capture, monotonic wait, and tracked terminal release verification.

## Frozen native first outcome

Before native execution, exact candidate source was published and frozen by Git
blob identity. Container construction had only compiled the code and exercised
two pure encoding/key helpers; it made no native-support claim.

GitHub Actions run `35126266999` at execution head
`b5750d3156ba009e727a794d74ed7e15edec438a` ran once on Microsoft Windows
Server 2025 (`10.0.26100`, image `windows-2025-vs2026`, CPython 3.12.10):

- pure helpers: **2/2 PASS**;
- native integration: **8/8 PASS**.

The valid path used a real native top-level HWND fixture. The backend focused the
window, moved/clicked the pointer, injected Unicode text and Ctrl+S, captured a
300x140 client region through GDI, and ended with verified empty tracked key and
button state. The independent fixture—not the backend—retained the exact effect
`{saved:true,text:"office",clicked:true}`.

Negative controls all passed with zero task input/effect:
- stale observation;
- stale binding revision;
- expired lease;
- unknown/stale target HWND rejected by native preflight;
- explicit surrogate code point rejected before Unicode input;
- unsupported `screen_logical` frame rejected by the shared core contract.

No same-identity native rerun occurred before this result.

## Scope limit

This is native execution evidence for one hosted Windows Server desktop/session,
not a general Windows population guarantee. Secure desktop, elevated/UIPI
boundaries, privileged apps, IME composition, natural focus contention and
mixed-DPI multi-monitor behavior remain outside v1 unless separately exercised.
The backend uses explicit HWND registration; accessibility/window discovery is
not required for the correctness floor.

The 2026-09-17 Research Preview RC remains separately frozen and is not changed
by this post-preview backend promotion.
