# HYPOTHESIS / FREEZE

Issue #59 construction hypothesis: the exact current-main V39 `DoomCoverSignalPairMonitor` typed-observation branch can use an epoch-coherent captured health/ammo pair to invalidate a hard health breach without calling artifact readers. A soft within-envelope change should preserve the current policy; mismatched or changed duplicate epochs should fail closed.

Treatment: direct typed-observation dictionaries passed to the exact extracted monitor methods from current-main commit `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

Controls: soft health 55 from source 59 with hard minimum 51; ammo/health sequence mismatch; duplicate sequence with changed health. No model, renderer, image, Doom, executor, OS input, or live allocation.

Decision rule: PASS only when hard health 48 produces `health:below_hard_minimum` with `requires_new_decision=true` and no input authority, soft change returns no invalidation, and both coherence violations invalidate fail-closed.

This construction cannot establish that a live threat is represented by HUD health, that the event is emitted early enough in the integrated V39 reader loop, that cancellation releases real input, or that task progress improves.

### Candidate-v3 interpretation correction

The first candidate assertions incorrectly expected an invalidated or soft typed-only sample to advance last_pair_sequence. Current main intentionally advances coherent-pair custody only when a matching artifact observation confirms the same epoch. The preserved candidate v1/v2 outputs document this correction; candidate v3 checks the typed-first then matching-artifact transition explicitly.
