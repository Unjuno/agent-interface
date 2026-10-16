# Adaptive semantic repair live v2

## Question

Can the shared adaptive caller execute its measured local repair and its typed
model fallback on real Chromium/X11 state changes while preserving current
evidence, independent task scoring, complete model accounting and input release?

This is an integration study. The two mutations are intentionally different, so
their latency and token totals are descriptive and are not a causal comparison.

## Retained v1 failure

V1 ran once on seed216. Its width-resize case reached
`reuse association_changed -> local repaired` with zero repair model calls, then
stopped before Submit. The final adapter had incorrectly required the completion
crop before the action that creates it. The exact current crop was materialized,
the binding was `CURRENT_EXACT`, and the semantic result was the required
`expected_crop_missing` pre-action state. No task Submit occurred, independent
output stayed empty and every input program released. The model-fallback case
never started. Forty files / 742,028 bytes pass the retained diagnosis on
Windows and WSL. V1 was not rerun.

## Frozen v2 change

V2 changed only final semantic admission. It requires:

- exact or translated current binding;
- a materialized current crop;
- `expected_crop_missing` before Submit;
- current target-patch resolution and ordinary Executor admission;
- the original post-action semantic predicate and independent POST scorer.

Seed217, local/model order, one allocation and zero retries were frozen before
execution. The local case changes the window width by -120 pixels. The fallback
case moves the pointer over the real Save button, changing its rendered patch.

## First v2 outcome

Both cases passed their first and only allocation.

| Case | Observed shared-caller route | Total calls | Input tokens | Images | Mutation capture to caller return | Submit admission to useful feedback |
|---|---|---:|---:|---:|---:|---:|
| Window resize | association_changed -> local repaired | 1 initial, 0 repair | 9,348 | 1 | 651.634ms | 248.037ms |
| Save hover | association_changed -> local missing -> model target -> current patch match | 1 initial, 1 repair | 18,696 | 2 | 7,871.585ms | 249.006ms |

The fallback's accounted repair-model wait was7,197.203ms. Its later target
sequence advanced beyond the model-visible mutation source before final
revalidation and input. Useful probe compute was2.730ms local and3.308ms model.
Both cases independently saved exact `t000217`, reconciled useful semantic
feedback and verified empty release for every input program. The model case
recorded the natural local discriminator as `missing`; it did not enter fallback
from a scripted branch label.

The pre-receipt record contains100 files / 1,792,829 bytes. Formal and retained
audits pass on Windows and WSL; the retention decision is
`RETAIN_PASSED_FIRST_OUTCOME_NO_RETRY`.

## Meaning and limits

This establishes that the shared caller can carry a current cached target
through a real local resize repair and can safely escalate one real changed
target patch to the same Luna-low model, revalidate after the wait, act once and
verify the effect. It also establishes false-versus-unavailable precondition
semantics in this composed path.

It does not estimate a natural repair/fallback rate, compare the two routes
causally, prove general token savings, cover unknown layouts or decoys, transfer
to another application, or establish human-tempo control. The next test should
add an action/effect/recovery provenance receipt to retained target crops and
freeze a held-out action-crop versus full-frame versus no-memory comparison.
