# Issue #57 R13: foreground physical-frame Edge Win32 caller composition

Date: 2026-11-23 (Asia/Tokyo)

## Question

Can the current-main V5 handle mint → standard caller v3 → compiled GUI task
path succeed with native Win32 input when all visual evidence is captured
from the foreground HWND's physical screen client rectangle, and safely
refuse the next action after same-window document generation changes?

## Frozen scope and safeguards

- Base: current `origin/main` `6cd2fd2d20c713849e48b3d2bae3e8aa6fad3bb3`.
- R13 is a new run identity. R10–R12 setup stops remain preserved; no run
  identity is repeated. Execute once in standard Python and once in `python
  -O`, with separate positive and changed-generation cases in each.
- Edge is visible on a loopback-only fixture using a per-case random profile
  and title. Verify exactly one visible title match whose live Edge process
  ancestry carries that profile.
- Record the original foreground HWND. Focus only the verified Edge HWND,
  then read its physical `ClientToScreen` origin and client size. Use
  `Win32Backend.capture_pixels(..., "screen_physical_px", x, y, w, h)` to
  BitBlt precisely that client rectangle. Require 756×488 capture dimensions
  equal to client geometry. These pixels, the V5 patch mint, OCR/effect checks
  and `window_client` input share the same physical point mapping.
- `PrintWindow` and CDP screenshots do not contribute to visual evidence. CDP
  supplies navigation, frame/loader metadata, controlled same-window reload
  and shutdown only. No CDP task input is available in the runner.
- Before each action, the caller adapter requires OCR to confirm the target
  field or submit control. Missing/unknown target presence refuses before
  dispatch. No model/provider calls, MAP01, Calc or user data; fixture task
  requests are local. Ambient browser egress is not measured.
- Cleanup may stop only Edge processes with that case's unique profile path;
  restore the original foreground HWND if still valid.

## Required outcomes

Positive: exactly one exact local POST and `TASK_SUCCEEDED`; two completed
compiled transitions; a verified terminal release receipt and stable,
bracketed left-button-up `GetAsyncKeyState` evidence after each; verified final
release and button-up; profile cleanup and foreground restoration.

Changed generation: native text entry followed by reload of the same target,
changing loader ID; exactly one completed action; then
`SCOPE_MISMATCH/window_generation_changed_or_missing`; no later native input,
POST or outer score. Require the same release, readback and cleanup evidence.

Any screen overlap, stale/ambiguous HWND, geometry mismatch, black/flat frame,
OCR miss, unknown release state, unexplained request or cleanup failure is a
STOP/FAIL. A pass is local fixture evidence only; it does not establish
provider economics, efficiency, reliability, queue quiescence,
arbitrary-application control, Research Preview graduation or product
readiness.
