# Issue #57 R11: visible Edge Win32 caller composition

Date: 2026-11-23 (Asia/Tokyo)

## Question

Does current-main V5 handle mint → standard caller v3 → compiled GUI
composition work with native Win32 `SendInput`, verifiable input release, and
same-window generation-change refusal after fixing R10's window ownership
discovery setup failure?

## Frozen setup

- Base remains current `origin/main` `6cd2fd2d20c713849e48b3d2bae3e8aa6fad3bb3`.
- The harness is a new run identity. R10's STOP packet remains immutable and
  is not retried or reclassified.
- Run once in standard Python and once under `python -O`; each has one positive
  and one changed-generation case. No retries within a case or mode.
- Edge uses a fresh random user profile and a loopback-only task form/scorer.
  The visible top-level window title is a per-case random value. Before
  accepting its HWND, discover its owning PID from Window APIs and verify that
  its live `msedge.exe` process ancestry contains this case's exact profile
  path. Require exactly one matching visible window.
- Fixed fixture points seed the V5 mint. All mouse/text task input uses
  `Win32Backend.execute` and `SendInput`; CDP is used only for navigation,
  screenshots, loader ID, negative-case reload and shutdown.
- No provider/model integration or calls, MAP01, Calc or user data. Task
  traffic is loopback-only. Chromium background networking, sync and component
  updates are disabled; ambient browser egress is not instrumented.
- Scoped cleanup may stop only Edge processes bearing the case's unique
  profile path. Restore the foreground HWND captured before each case if it is
  still valid.

## Required outcomes

Positive: `TASK_SUCCEEDED`, exactly one exact local POST, two native task
operations and two completed compiled transitions. Each operation must have a
verified terminal release receipt and a bracketed, stable
`GetAsyncKeyState` left-button-up readback witnessed across the same
foreground/input desktop. Final release and final button-up readback must
also pass.

Changed generation: after native text-entry, reload the same document so its
loader ID changes. Require one completed operation, then
`SCOPE_MISMATCH/window_generation_changed_or_missing`; no second native input,
POST or outer success score; and the same release evidence after the first
operation and at final cleanup.

Both modes require scoped profile deletion, foreground restoration where the
original HWND remains valid, empty cleanup errors, and retained hashes,
screenshots/OCR, admissions, caller receipts, exact POST bodies and native
release/readback records. Any missing or unknown release observation is a
STOP/FAIL; it cannot count as success.

## Limits

Even a pass is a local fixture composition result only. It does not prove
provider economics, matched efficiency, reliability rate, application queue
quiescence, arbitrary-app control, Research Preview graduation or product
readiness.
