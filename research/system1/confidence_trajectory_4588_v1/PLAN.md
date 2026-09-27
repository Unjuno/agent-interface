# Confidence-trajectory System-1 — first-rung experiment

Issue: [#4588](https://github.com/Unjuno/agent-interface/issues/4588)
Allocation: `confidence-trajectory-4588-first-rung-20260927-01`
Scope: synthetic, deterministic, authority-neutral discriminator only.

## H — hypothesis

On a deliberately finite temporal corpus, causal confidence velocity and
acceleration can distinguish cases that current confidence alone (and, for a
second-order alias, velocity alone) cannot. A raw acceleration rescue rule may
also admit a deliberately oscillatory/noisy false action. A frozen causal,
time-weighted smoother may reject that stress case but miss a low-confidence
useful rise. `NO_OP` must remain a distinct output from `YIELD`.

This is the Issue's model-free first rung. It compares transparent fixed rules,
not learned model capacity, GUI perception, or action authority.

## T — treatment and frozen allocation

- Environment: local OrbStack image `python:3.13-slim`, immutable ID
  `sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0`
  (`linux/arm64`); Docker Engine `29.4.0`; `--pull=never`, `--network none`.
- One invocation over 84 fixed rows: 14 scenario families × 6 deterministic
  perturbations. The six second-order-alias pairs share current confidence and
  latest velocity while differing only in the earlier sample and thus
  acceleration. Irregular intervals, oscillatory/noisy input, stale/missing
  history and epoch mismatch are explicit rows.
- Same single candidate, intent scope, current state and typed output vocabulary
  across four policies: `CURRENT_ONLY`, `LEVEL_PLUS_VELOCITY`,
  `LEVEL_PLUS_VELOCITY_PLUS_ACCEL`, and `SMOOTHED_TRAJECTORY`.
- No fitting, tuning, random seed, future samples, GUI, input, model/provider,
  user data, or external network. All scores and labels are authored finite
  fixtures; the first rung does not claim a population sample.
- Invalid historical samples invalidate temporal features and explicitly fall
  back to the current-only rule. Current-state validity is held true in those
  cases; this does not renew or establish authority.
- Raw JSONL, environment, process exit, summary and audit output are retained.

### Frozen rules

Let `p0,p1,p2` be the three causal scores; `v1` and `v2` are adjacent changes
normalized per 100 ms; `a = v2-v1`. The smoothed score is the trapezoidal
time-weighted mean over the observed interval.

- Current-only: `ACTION` iff state is `ACTION_REQUIRED` and `p2 >= 0.75`.
- Velocity: current-only positive rule plus `ACTION` iff
  `p2 >= 0.55 and v2 >= 0.20`; a falling score below the current-only threshold
  yields `YIELD`.
- Acceleration: velocity rule's `ACTION` requires `a >= 0`, plus a frozen raw
  acceleration rescue iff `p2 >= 0.50, v2 >= 0.20, and a >= 0.50`.
- Smoothed: `ACTION` iff state is `ACTION_REQUIRED` and the causal trapezoidal
  mean is `>= 0.75`.
- For all policies, `SELF_CORRECTING -> NO_OP`, `UNCERTAIN -> YIELD`; non-current
  history is never consulted in those state branches. Missing/stale/epoch-
  mismatched history selects the current-only fallback for the three temporal
  arms and records that fallback in each row.

## D — first-rung decision gates

The result is `PASS_SYNTHETIC_DISCRIMINATOR_ONLY` only if all 84 inputs and four
policy outputs reconcile; the independent raw-only auditor has zero errors and
all eight effective copied-formal-row mutations are rejected; all six second-order
alias pairs have identical `CURRENT_ONLY` and `LEVEL_PLUS_VELOCITY` outputs,
while the acceleration arm separates both labels correctly; `NO_OP` is emitted
for all six self-correcting rows; and all invalid-history rows record explicit
current-only fallback with no temporal feature use; and the authored
oscillatory/noise stress shows the frozen acceleration-specific errors and
smoother response. On this authored corpus only, the acceleration arm must not
be less accurate or have more false executable decisions than current-only.

Metrics (typed accuracy, false executable count/rate, action precision/recall,
correct `NO_OP` and `YIELD` counts) are descriptive and reported for every arm.
Any gate miss is retained as `HOLD_FIRST_RUNG`; source/process/raw/audit
ambiguity is `STOP/HOLD`, not a scientific FAIL. No retries, row replacement,
pooling, or post-result tuning.

## C — competing explanations and limitations

The corpus is intentionally authored to contain discriminating examples and
does not estimate natural frequencies. Fixed transparent rules are not a
capacity-matched learned head. Finite differences are sensitive to sampling and
confidence calibration; the stress set is not an exhaustive noise model. The
time-weighted smoother and its threshold are one frozen comparator, not an
optimal filter. Same-author separate auditor is not external human review.

## U — scope and next gate

No conclusion about real GUI observations, model calibration, generalization,
task completion, human tempo, tokens/cost, production safety, or executable
authority follows. A scoped first-rung PASS only justifies a later frozen
shadow-mode transfer on real sequential observations with no action authority.
