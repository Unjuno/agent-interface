# In-trajectory observability successor — source freeze

Issue: #2476; parent: #729
Branch: `research/doom/intrajectory-observability-2476-v1`

## Frozen transfer factor

Keep the #729 scale-aware matcher, 0.80 acceptance threshold, ROI, pulse duration, correction limits, and fail-closed authority semantics fixed. Compare only observation policy: BASELINE full re-match, TRACKED bounded local corridor with typed track receipt, and ABSTAIN on corridor/age/geometry/confidence failure.

## Required evidence

Retain every raw frame hash, match score, predicted/observed displacement, search region, observation age, track state, correction/input receipt, final neutral key/button state, and independently scored task effect. Include aligned, missing, flat/ambiguous, target disappearance, and abrupt translation controls.

## Formal gate

One container-first first-result block after source, fixture, image digest, seeds, arm order, corridor, age, and stopping rule are frozen. No rerun, replacement, tuning, or pooling.

`PASS_INTRA_TRAJECTORY_OBSERVABILITY_SCOPED` requires improved held-out target-error completion, zero false continuation after disappearance/invalidation, every continuation inside the typed current track envelope, neutral terminal input, and independent source/result/audit integrity. Safe but incomplete tracking is HOLD; stale-track authority, false alignment, unsafe continuation, or integrity mismatch is FAIL.

## Non-claims

No arbitrary-GUI identity, model/token benefit, human tempo, production promotion, or semantic task generality claim. A PASS only authorizes later real-app transfer.