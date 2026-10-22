# Hypothesis and decision rule

## Question
Does the current-main typed ammo monitor, pending planner lifecycle, V39 invalidation/cancel ordering, Executor v13, and V4→V3→V12 input owner compose as intended at the two meaningful ammo boundaries when a fire cover is actively holding the key?

## Hypothesis
At ammo 4, above the cover's hard minimum 1 but below a synthetic immediate-action minimum 5, the monitor records a soft event and does not revoke the running cover. The pending answer remains eligible, and the actual current-main Executor and owner stack continue to hold the fire key until later cleanup. At ammo 0, the monitor invalidates; `cancel_invalidated_cover` must dispatch Executor cancellation before planner interruption; owner release must be verified empty; Executor v13 must publish release before terminal; and the answer tied to the invalidated observation must be ineligible.

## Frozen fixture
One authored fire-hold step, source health/ammo 97/8, paired sequence-2 observations (health 97, ammo 4 or 0), a fixed pointer binding, one synthetic planner completion, and a deterministic in-memory fake X server. The executor and owner Python source is copied byte-for-byte from current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

## Pass rule
The scoped construction pass requires both arms in one frozen run: soft arm has no invalidation, exactly one soft event, active Executor/key-down while the pending turn completes, and eventual verified cleanup; hard arm invalidates for `ammo:below_hard_minimum`, dispatches executor cancel before planner interrupt, yields an owner-reported verified-empty release, publishes `input_released` before terminal, leaves no fake key held, and rejects the pending answer. Any mismatch is a construction failure and is retained.

## Claim limits
The immediate-action floor is a declared synthetic contrast, not a live policy assertion. The fake XTest server validates software order and owner code paths only. No live model, Doom process, X server, OS input, physical release, useful feedback, bounded recovery, task effect, progress, or MAP01 outcome is tested. No allocation is requested or consumed.
