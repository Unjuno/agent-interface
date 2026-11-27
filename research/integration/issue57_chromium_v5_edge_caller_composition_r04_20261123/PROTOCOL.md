# Issue #57 Chromium V5 → caller v3 → compiled GUI R04

## Frozen rationale

R03 reached real Edge, V5 mint/revalidation, and its first CDP action, then
stopped because Windows OCR did not read the exact visible value. The retained
screenshot visibly contains `t991025-4`; three post-hoc crop/scale variants
also did not recover it. R04 changes only the controlled fixture's text
legibility (bold 26 px input, larger button, isolated OCR region). The exact
token criterion and independent HTTP POST scorer are unchanged. This is a
diagnostic controlled-browser experiment, not an application-general OCR
claim.

## Frozen question and limits

Can exact V5 point-derived handles from live Edge screenshots traverse the real
caller-v3/compiled-GUI path for two actions, while a reload-induced document
generation change refuses the second action?

- Base main: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- One positive and one changed-generation case in normal mode, then once with
  `python -O`. These modes do not count as independent repeats; do not retry
  within R04.
- Fresh headless Edge profiles and a loopback-only form. Fixture-known points;
  zero model/provider calls and no external network.
- CDP mouse press/release and `insertText`, not OS input. Pointer scope is the
  page/document adapter, not HWND focus. CDP release does not prove physical
  input release.
- Independent success requires the HTTP server to receive exactly the task
  token and the outer scorer to verify it.

## Pass criteria

Positive requires two exact-patch private aliases, successful caller
revalidation and two compiled admissions, exact OCR confirmation after entry,
two CDP actions/releases, one exact POST, independent scoring, and caller
`TASK_SUCCEEDED`.

Changed-generation requires the first action and exact OCR effect to survive a
same-target page reload, the changed loader generation to refuse Submit as
`SCOPE_MISMATCH/window_generation_changed_or_missing` before its execute
callback, caller `EXECUTION_INCOMPLETE` with one completed action, and no POST
or outer task-success verdict.

Any failed positive gate stops the allocation; later cases and mode runs are
not started. Preserve raw screenshots, conditions and source hashes, runner
outputs, receipts, effect scores, cleanup evidence and all failures. No
provider economics, reliability, OS release, MAP01/Calc, or distribution
claim follows.
