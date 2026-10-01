# Quartz runtime backend v1

Product-integration candidate for Issue #631. It composes the unchanged promoted `runtime/core_v1` admission contract with macOS ApplicationServices/CoreGraphics through Python stdlib `ctypes`.

V1 deliberately exposes only `screen_physical_px`; it does not fabricate window-client geometry. Explicit PID targets are the correctness floor. Accessibility and Screen Recording permission probes are part of the capability manifest: missing permission produces `permission_required`, never silent support.

Candidate capabilities: AX frontmost focus, Quartz keyboard/text, pointer/buttons, wheel scroll, display geometry/capture, monotonic wait, and tracked release verification.

The native integration fixture launches the system `osascript` `display dialog` command. The backend types into that native dialog; the wrapper independently retains the returned text as the task effect. Promotion requires that native app effect, actual screen capture, physical cursor readback, verified release, and all frozen zero-event controls pass on macOS.

This v1 evidence does not establish signed/notarized packaging, sandbox/TCC persistence, secure input, IME, multiple displays/Spaces, privileged applications, or natural focus contention.
