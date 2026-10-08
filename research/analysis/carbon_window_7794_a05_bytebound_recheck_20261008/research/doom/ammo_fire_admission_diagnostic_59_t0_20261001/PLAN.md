# MAP01 ammo/fire diagnostic T0 — Issue #59

## H / T / D / C / U

- **H:** In the retained v38/v39 first outcomes, complete `space` hold steps with an observed positive ammo value before the step show a sampled ammo decrease during a greater share of steps in v39 than v38. A submitted attack step that never reaches the exact `keys_held` keyset must not be counted as a confirmed firing step.
- **T:** On current-main frozen inputs only, pair each submitted `space` hold with its step start, per-key admission, `keys_held`, typed ammo observations and terminal boundary. For normally completed steps, use the independently identified observation sequence: all same-step observations except the final post-release observation are in-loop; join those sequence/capture pairs to typed ammo values. Keep interrupted and partial-admission steps separate from the completed-step contrast. Reconcile v38 and v39 independently from raw events.
- **D:** Measurement integrity requires matching source hashes, classification of every started `space` step, exact requested/admitted/held-keyset joins for each completed attack step, a pre-step typed ammo reading, and at least one exact-joined in-loop ammo sample for each completed attack step. `PASS_DIAGNOSTIC_CONTRAST_SCOPED` additionally requires all completed attack steps to begin with positive observed ammo and the v39 completed-step ammo-decrease fraction to strictly exceed v38. Integrity failures are `FAIL_INTEGRITY`; a valid non-positive contrast or zero-ammo step is `HYPOTHESIS_NOT_SUPPORTED`. Report unknown/zero ammo and incomplete attempts separately.
- **C:** This is a descriptive audit of two different stochastic MAP01 episodes, not a matched intervention. Ammo may change for reasons not uniquely attributable to one key-hold, sampled HUD values are discrete, and held-input termination is interval-censored. `space` admission and ammo decline do not establish that a shot hit a threat, that the policy was tactically appropriate, or that ammo use improved survival/progress.
- **U:** No causal firing efficacy, target identification, task usefulness, death prevention, live controller improvement, MAP01 exit, speedup, or human-tempo claim. No model/game/GUI/input/container call is authorized by this analysis.

## Frozen estimand and evidence boundary

Primary estimand: among normally completed steps whose declared key set includes `space` and whose exact `keys_held` marker confirms that declared set, the proportion with at least one in-loop typed ammo value below the latest typed ammo value captured before `step_started`. A typed observation is matched by exact sequence and capture timestamp to its same-step pixel-observation row. The final same-step observation before `step_completed` is excluded because the pinned runtime/occupancy reconstruction identifies it as post-release.

All `space`-declared starts are additionally classified as full-keyset-confirmed, interrupted after full keyset, partial/unconfirmed, or integrity error. Interrupted and partial rows are not silently treated as completed attack observations. Report their ammo evidence separately, with no efficacy inference.

## Execution

Use Python host-only because this is a deterministic raw-log computation; the shared container lane has an explicit owner and is not available to this task. Run unit tests before the one formal raw computation. The candidate consumes each frozen v38/v39 raw file once; a separate auditor independently re-parses those raw files and the candidate JSON. No retry, no source/result overwrite, and no raw log copied or altered.
