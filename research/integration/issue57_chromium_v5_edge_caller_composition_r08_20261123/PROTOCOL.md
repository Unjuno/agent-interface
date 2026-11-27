# Issue #57 Chromium V5 → caller v3 → compiled GUI R08

## Frozen rationale

R07's normal-mode positive and changed-generation functional outcomes matched
their gates, but Edge child processes retained both temporary profiles and
made the runner exit 1. Exact-profile process termination was manually
verified after that run. R08 adds scoped cleanup to this test runner: after
closing the owned Edge browser, terminate only `msedge.exe` processes whose
command line contains the exact generated profile path, then run the existing
profile deletion helper. The OCR completion-banner normalization from R06/R07
is unchanged. R07 remains immutable.

## Question and limits

Can the composed local Edge path pass its exact-task positive case and refuse
a changed-generation action, while the runner cleans each generated profile,
in both normal and optimized Python?

- Current-main base: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- Run both cases once normally and once with `python -O`, fresh profiles each
  time. The four executions are mode checks, not independent reliability
  trials. Stop after any failure.
- Headless Edge, loopback-only local form, actual screenshots and Windows OCR,
  fixed known fixture points, zero model/provider calls.
- CDP input only; no OS-level delivery or physical release evidence.

## Pass criteria

Positive case: exact token OCR, exact single local POST, matching independent
score, and `TASK_SUCCEEDED` from caller. Changed-generation: exact task value
retained across same-target reload, loader generation changed, compiled
admission refuses with `SCOPE_MISMATCH/window_generation_changed_or_missing`
before dispatch, `EXECUTION_INCOMPLETE`, one completed action, and no POST or
outer score. Every case also records `profile_cleaned: true` with no cleanup
error and no Edge process referencing that profile.

Retain all raw and failures. This cannot establish native input release,
provider cost, repeated reliability, Calc/MAP01, matched efficiency, or public
runtime readiness.
