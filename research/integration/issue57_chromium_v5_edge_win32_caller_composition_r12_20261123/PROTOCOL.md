# Issue #57 R12: native-frame Edge Win32 caller composition

Date: 2026-11-23 (Asia/Tokyo)

## Question

Can the current-main V5 handle mint → standard caller v3 → compiled GUI path
complete a local form task through native Win32 input when point evidence and
OCR come from the same Win32 window-client pixel frame, and refuse a later
action after same-window document generation changes?

## Frozen scope

- Current `origin/main` base: `6cd2fd2d20c713849e48b3d2bae3e8aa6fad3bb3`.
- R12 is a new run identity after R10/R11 setup stops. It runs once under
  standard Python and once under `python -O`; each mode includes independent
  positive and changed-generation cases. No same-case retries.
- Each case starts a visible Edge instance with a unique profile and an
  isolated fixture served on loopback. A random page title plus process
  ancestry must identify exactly one visible HWND owned by this profile.
- **Every pixel image used for V5 minting, caller observations, OCR and
  effect verification is captured from `Win32Backend.capture_pixels` in the
  same `window_client` frame as the native input coordinates.** The
  756×488 image dimensions must equal the Win32 client geometry.
- Task mouse/text input uses only `Win32Backend.execute`/`SendInput`. CDP is
  limited to initial navigation, passive frame/loader metadata, controlled
  same-target reload in the negative case and shutdown. No CDP screenshot or
  CDP input contributes to point/effect evidence.
- Before authorizing each action, the caller adapter also requires OCR to
  confirm the intended field or submit control is present in the native
  capture. Unknown/missing control evidence refuses before dispatch.
- No model/provider integration or calls, MAP01, Calc or user data. Task
  traffic is loopback-only. Ambient browser egress is not instrumented.
- Cleanup can stop only Edge processes with this case's unique profile path;
  restore the prior foreground window if its HWND remains valid.

## Required outcomes

Positive: one exact local POST, caller `TASK_SUCCEEDED`, two completed
compiled transitions, and for each native action a verified terminal release
receipt plus stable, bracketed `GetAsyncKeyState` left-button-up evidence.
Final cleanup must also verify release/button-up and scoped profile cleanup.

Changed generation: native field entry followed by same-target reload changing
the loader ID; one completed action; then
`SCOPE_MISMATCH/window_generation_changed_or_missing`; no second native action,
POST or outer score. Release/button-up and cleanup criteria match the positive
case.

Any capture failure, OCR target miss, coordinate mismatch, unknown release
state, unexpected foreground, evidence gap or cleanup error is STOP/FAIL. A
pass only covers this local fixture path and does not establish provider
economics, matched efficiency, reliability rate, queue quiescence, arbitrary
application control, preview graduation or product readiness.
