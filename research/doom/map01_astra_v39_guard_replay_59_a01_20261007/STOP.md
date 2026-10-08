# STOP — duplicate prior evidence

**Disposition: `STOP_DUPLICATE_PRIOR_EVIDENCE`.**

After the one-shot candidate and independent auditor completed, GitHub MCP review found two earlier #59 packages that already answer this question more strongly:

1. [`v28_health_envelope_counterfactual_a01_20261005`](../v28_health_envelope_counterfactual_a01_20261005/README.md) replays the current V39 health/ammo guard across five retained spans and all 21 supported `maximum_health_loss` budgets (0–20), with an independent auditor. It already reports which budgets invalidate the paired snapshots.
2. [`v39_current_main_paired_guard_replay_a01_20261005`](../v39_current_main_paired_guard_replay_a01_20261005/README.md) processes 52 exact retained health/ammo events through the current-main paired monitor, including the first hard crossing and invalidation classification.

This A01's selected manually transcribed Astra HUD samples and 12 hypothetical health-floor combinations are therefore not a distinct unresolved test. They are weaker than the existing analyses: only ten sparse selected values, no paired dense ammo stream, no exact historical guard policy, and no current V39 controller in the old episode. The computed scenario table remains preserved solely to record the redundant run; its `PASS_SCENARIO_REPLAY_ONLY` field is a deterministic process-level status, not an accepted research result.

Candidate invocation 1/1 and independent auditor invocation 1/1 completed before the duplication was discovered. The eight construction tests passed. No candidate/auditor rerun was made. A subsequent construction-test Docker launch with an invalid image digest was rejected before container startup; this STOP is retained in `RUN_RECORD.json` and does not alter the completed one-shot outputs.

No new scientific claim, threshold recommendation, actual V39 interruption, or live-control evidence follows. The prior packages remain unchanged and authoritative. Fresh live Issue #59 allocation remains separately unassigned; this STOP does not authorize one.
