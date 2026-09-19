# Runtime interface v1 native-probe facade

Task `RUNTIME-NATIVE-PROBE-FACADE-20260917-001`, Issue #596.  
Integration base `5c7420e4284fcca0cf05b824c21da02ad03ea15d`.

Decision: **PASS_LOCAL_NATIVE_PROBE_FACADE_CANDIDATE** pending the exact
Windows/macOS/Ubuntu hosted-runner matrix.

## Purpose

Provide one side-effect-free user-facing doctor across Linux, Windows and macOS
without turning native API presence into an automation support claim.

The facade always returns `support_claim=false`, `ready_for_side_effects=false`,
`input_authority=none` and `capture_authority=none`. Native effect support remains
a separate backend promotion gate.

## Platform probes

- Linux: reuses the promoted core platform probe, identifies X11/Wayland/none and
  records that the X11 adapter is an integrated candidate only.
- Windows: loads `user32` through stdlib `ctypes`, checks API presence and reads
  system metrics / whether a foreground handle is observable. It emits no input.
  Because there is no separately proven native effect backend, desktop automation
  permission/readiness remains `unknown`.
- macOS: loads CoreGraphics and ApplicationServices through stdlib `ctypes`, reads
  display geometry when available, calls `AXIsProcessTrusted` and
  `CGPreflightScreenCaptureAccess` when exported. It never prompts for permission,
  emits no input and captures no screenshot. Permission absence remains explicit.

## Local construction result

Exact source passes compile plus **6/6 tests**. The local Linux doctor observed an
X11 candidate but still returned no side-effect authority. A clean-copy rerun of
the exact source passed the same 6/6 tests and JSON safety assertions.

## Scope

This result is a discovery/doctor contract only. It does not promote Win32 or
Quartz input/capture, Wayland, general X11/WSLg support, installation packaging,
or end-to-end user task correctness. Those require effect-owning backend lanes.
