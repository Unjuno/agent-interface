# MAP01 door action-effect history v2 — retained replication

## Decision

**`SUPPORT_ACTION_EFFECT_HISTORY` + `PASS_FULL_REPLAY`.**

V2 is the retention-only successor to consumed v1. The scientific crop, classifier, tics, alias threshold, train/held-out sizes, yaw/wait schedule and numeric effect gates are unchanged. V2 changes only: disjoint formal seeds, retention of each measured current frame's immediate predecessor, and a mandatory independent raw replay audit.

## Formal result

Twenty fresh direct-ViZDoom MAP01 cases (`994200..994219`) produced 320 measured states and 640 raw PNGs (current + predecessor). The first 12 cases define the fixed opening/closing centroids; the last 8 are held out.

All eight held-out cases exposed a preregistered near-aliased opening/closing pair (`current RMSE <= 0.005`). On the resulting 16 alias observations:

- current-view-only accuracy: **0.500**;
- one-step visual delta/history accuracy: **1.000**.

Across all 128 held-out observations:

- current-view-only accuracy: **0.625**;
- one-step history accuracy: **0.71875**.

Current descriptors contain three exact cross-label collisions; history descriptors contain zero.

The independent audit decodes all 640 PNGs, verifies their RGB hashes, reconstructs every descriptor and one-step delta, independently re-selects the alias pairs, retrains the frozen centroids from the retained train cases, and reproduces the formal current/history accuracies exactly. Audit disposition: **`PASS_FULL_REPLAY`**.

## Interpretation

This supports one narrow mechanism: **a short action/effect history can identify task state when the current visual observation alone is aliased**. The evidence does not show that history alone solves MAP01 navigation; the prior visual-generalization study already shows long-horizon place recognition and local action selection remain separate errors.

The next useful rung is no longer another classifier threshold sweep. It is to feed a bounded history key into a small observable-input execution problem and require an independently scored task-relative effect before semantic state advances.

## Scope / forbidden extrapolations

Direct ViZDoom teacher/evaluator mechanics only. No OS-input efficacy, no frontier-model result, no MAP01 clear, no general GUI improvement, no long-horizon causal navigation claim.
