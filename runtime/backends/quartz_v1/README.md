# Quartz runtime backend v1

Product-integration candidate for Issue #631. It composes the unchanged promoted `runtime/core_v1` admission contract with macOS ApplicationServices/CoreGraphics through Python stdlib `ctypes`.

V1 deliberately exposes only `screen_physical_px`; it does not fabricate window-client geometry. Explicit PID targets are the correctness floor. Accessibility and Screen Recording permission probes are part of the capability manifest: missing permission produces `permission_required`, never silent support.

Candidate capabilities: AX frontmost focus, Quartz keyboard/text, pointer/buttons, wheel scroll, display geometry/capture, monotonic wait, and tracked release verification.

The native integration fixture launches the system `osascript` `display dialog` command. The backend types into that native dialog; the wrapper independently retains the returned text as the task effect. Promotion requires that native app effect, actual screen capture, physical cursor readback, verified release, and all frozen zero-event controls pass on macOS.

This v1 evidence does not establish signed/notarized packaging, sandbox/TCC persistence, secure input, IME, multiple displays/Spaces, privileged applications, or natural focus contention.

Persistent `QuartzRuntimeSession` owners must retain `recovery_required` after
an unverified/missing release or an execution exception without a verified
release receipt. Ordinary follow-up dispatch then returns
`INPUT_RECOVERY_REQUIRED` before admission or backend access. Updated images,
binding revisions, direct backend cleanup and edits to returned receipts do not
clear the session latch. A verified receipt requires literal `verified: true`,
empty down-state lists and no reported unknown controls or cleanup errors.

This session has no automatic reset or program replay. It does not expose a
verified recovery operation; new session construction or direct latch mutation
is not proof of physical neutrality. Cross-session/backend ownership, native
failure observation, process/host restart and fresh verified re-admission remain
open under #2437. The latch transfers the existing X11 fail-closed policy;
inert regression tests do not establish physical release or task effects.
