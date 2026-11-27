# Issue #57 Chromium V5 → caller v3 → compiled GUI R09

## Frozen rationale

R07's normal functional outcomes passed but its test failed profile-cleanup
assertions because Edge child processes held generated profile directories.
R08 attempted to add exact-profile process cleanup, but preflight compilation
found an indentation error; no tests ran and Edge did not launch. R09 evaluates
the corrected source. Cleanup remains limited to `msedge.exe` command lines
containing the exact unique profile path, followed by the existing validated
profile deletion helper. OCR banner normalization and task/effect conditions
are unchanged.

## Question and limits

Can the composed local Edge path pass its exact-task positive and changed-
generation cases, with profile cleanup, in normal and optimized Python?

- Current-main base: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- Run both cases once in normal Python and once with `python -O`, each using
  fresh Edge profiles. These are mode checks, not reliability repetitions.
  Stop on first failure.
- Headless Edge, loopback-only form, real screenshots and Windows OCR, fixed
  known fixture points, zero model/provider calls.
- CDP input only; no OS-level delivery or physical release evidence.

## Pass criteria

Positive: exact token OCR; exactly one exact `value=t9910254` POST; matching
independent score; caller `TASK_SUCCEEDED`. Changed-generation: loader changes
after reload; compiled admission refuses with
`SCOPE_MISMATCH/window_generation_changed_or_missing` before submit dispatch;
caller `EXECUTION_INCOMPLETE`, one completed action, and no POST or outer
score. Every case has `profile_cleaned: true`, no cleanup error, and zero
remaining Edge processes referencing its profile.

Retain all raw output. This cannot establish native input release, provider
cost, repeated reliability, Calc/MAP01, matched efficiency, or public runtime
readiness.
