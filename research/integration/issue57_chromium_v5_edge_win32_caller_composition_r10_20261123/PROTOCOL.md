# Issue #57 R10: visible Edge and Win32 caller composition

Date: 2026-11-23 (Asia/Tokyo)

## Question

Does the current-main V5 handle mint → standard caller v3 → compiled GUI
composition produce one exact local task effect using the native Win32
`SendInput` backend, retain verifiable release evidence, and refuse a later
action after same-window document generation changes?

## Frozen scope and setup

- Base: current `origin/main` `6cd2fd2d20c713849e48b3d2bae3e8aa6fad3bb3`.
- Run the committed harness once under standard Python and once under
  `python -O`; each mode has one positive and one changed-generation case.
- Launch visible Microsoft Edge in a unique temporary profile against a
  fixture served only from `127.0.0.1`. The fixture has one text field and one
  submit button. Each case gets a fresh randomized local port and profile.
- Fixed fixture coordinates seed the existing V5 point mint; this is not a
  model-point experiment. Capture/OCR/effect checks remain local.
- All task mouse and text input goes through `Win32Backend.execute` and
  `SendInput`. CDP is limited to navigation, screenshots, page-loader ID
  capture, same-target reload in the negative case, and shutdown.
- No provider/model integration or calls, MAP01, Calc, or user data. The exact
  task form/scorer traffic is loopback-only. Chromium background networking,
  sync and component updates are disabled; ambient browser egress is not
  instrumented and will not be represented as measured.
- Keep every run packet, including stop/failure outcomes. No retries within a
  case or mode. Cleanup may terminate only Edge processes whose command line
  contains that case's unique profile path. Restore the foreground window that
  was active before the case when that HWND remains valid.

## Cases and required evidence

Positive: submit the exact token once through the standard caller. Require
`TASK_SUCCEEDED`, one exact raw local POST, exactly two dispatched task
operations, two completed compiled transitions, a verified native terminal
release receipt and witnessed left-button-up after each operation, plus
verified final release and a final witnessed left-button-up.

Changed generation: after native entry input, reload the same target document
to change the Chromium loader ID. The token persists only in this isolated
fixture's `localStorage`. Require exactly one completed operation, caller
`EXECUTION_INCOMPLETE`, `SCOPE_MISMATCH/window_generation_changed_or_missing`
on the next admission, no second native dispatch, no POST, no outer success
score, and the same per-operation/final release evidence as above.

Both cases also require scoped Edge-profile cleanup, empty cleanup-error
lists, source/condition hashes, retained screenshots/OCR/admission/caller
receipts, exact raw POST bodies and the mode flag in each `run.json`.

## Stop and pass rules

Any mismatch, missing/unknown physical release readback, invalid target scope,
unexpected foreground target, non-loopback request, profile cleanup failure,
or missing evidence is a failed/stopped trial, never a pass. Preserve the
packet and do not repeat it under the same run identity. R10 is a scoped
native-input composition experiment; it cannot establish provider economics,
efficiency, a reliability rate, application-queue quiescence, arbitrary-app
control, Research Preview graduation, or product readiness.
