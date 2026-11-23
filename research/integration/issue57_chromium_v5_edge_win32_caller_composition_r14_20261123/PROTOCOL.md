# Issue #57 R14: CUA activation with Win32 physical capture/input

Date: 2026-11-23 (Asia/Tokyo)

## Question

Does V5 handle mint → standard caller v3 → compiled GUI succeed on a local
Edge task through Win32 input once the verified target is activated by the
permitted computer-control UI, with same-frame physical screen pixels and
fail-closed refusal after generation changes?

## Frozen scope

- Base: current `origin/main` `6cd2fd2d20c713849e48b3d2bae3e8aa6fad3bb3`.
- New R14 run identity after R10–R13 stops. Run once in standard Python and
  once in `python -O`; separate positive and changed-generation cases; no
  same-case retries.
- A visible Edge app window uses a fresh random profile, random title and
  loopback-only fixture. The runner verifies its exact HWND owner and profile
  ancestry, then emits a per-case `activation-request.json` and pauses before
  capture, minting or task input.
- Using CUA, inspect that exact title/window and click only blank page space
  (never the input field or Save button). Record the CUA window ID and time in
  `activation-confirmed.json`. The runner then independently verifies that
  this HWND (or its root) is actually foreground before proceeding. No
  programmatic focus escalation or OS focus-policy bypass is used.
- After activation, capture the exact HWND client rectangle from the physical
  desktop using Win32 BitBlt. Require dimensions to match
  `Win32Backend.geometry`. Use this same pixel frame for V5 patch mint, OCR,
  effect checks and the `window_client` Win32 input coordinates. CDP is
  restricted to navigation, loader metadata, same-target reload and shutdown.
- Before every action, require OCR target presence; unknown/missing evidence
  refuses before input. Input goes only through `Win32Backend.execute` and
  `SendInput`.
- No model/provider integration or calls, MAP01, Calc or user data. Ambient
  browser egress is not instrumented. Cleanup terminates only Edge processes
  bearing that case's unique profile path and restores the prior foreground
  HWND if still valid.

## Required outcomes

Positive: exactly one exact local POST, caller `TASK_SUCCEEDED`, two completed
compiled transitions, verified terminal release receipt and stable bracketed
left-button-up `GetAsyncKeyState` readback after each operation, plus verified
final release, profile cleanup and foreground restoration.

Changed generation: one native entry action, same-window reload changing the
loader ID, then `SCOPE_MISMATCH/window_generation_changed_or_missing`; no
second native dispatch, POST or outer score; the same release and cleanup
criteria apply.

Any CUA scope mismatch, activation failure, desktop occlusion, coordinate or
OCR mismatch, unknown release state, unexpected request, or cleanup error is
STOP/FAIL. Even a pass is local fixture evidence only and does not establish
provider economics, efficiency, reliability, queue quiescence, arbitrary-app
control, preview graduation or product readiness.
