# Retained Astra HUD replay against current V39 health-guard semantics — A01

**Final disposition: `STOP_DUPLICATE_PRIOR_EVIDENCE`.** The post-run GitHub audit found this question is already covered more strongly by #59's [`v28_health_envelope_counterfactual_a01_20261005`](../v28_health_envelope_counterfactual_a01_20261005/README.md) (all 21 supported health-loss budgets over five retained spans) and [`v39_current_main_paired_guard_replay_a01_20261005`](../v39_current_main_paired_guard_replay_a01_20261005/README.md) (52 exact retained health/ammo observations replayed through the current paired monitor). This A01's 12 threshold scenarios use only ten sparse, manually selected HUD samples and add no distinct unresolved evidence. Preserve its candidate/audit outputs as a duplicate-run receipt only; do not cite its process PASS as a new scientific result or combine it with predecessor evidence.

The candidate and independent audit were each invoked once before discovering the duplication. No rerun occurred. See `STOP.md` for the comparison and correction. The prior GitHub results remain authoritative; this package does not amend or supersede them.

## H / T / D / C / U

**H.** Applying the current-main V39 health guard's documented strict hard-floor rule to selected health values from the retained Astra decision-4 video can identify which hypothetical authored threshold pairs would first request a new decision in the sampled pending interval, and which would not be observed until after the model-return boundary.

**T.** Freeze the ten manually transcribed samples from `VISUAL_READOUT.json` in `fixture.json`; replay 3 critical-health minima × 4 maximum-loss values. Compute `hard_minimum = max(critical_health_minimum, source_health - maximum_health_loss)` with source health 100. A sample requests invalidation only when `health < hard_minimum`; equality remains valid. Classify the first below-floor selected frame as pending (≤56.2 game seconds), at/after return (≥56.4), or unobserved in this selected set. Candidate and independent raw-only auditor run once each in the pinned network-disabled container. No model, game, GUI, or input calls.

**D.** `PASS_SCENARIO_REPLAY_ONLY` requires all 12 scenarios to be independently reconstructed, strict equality behavior to match the production guard, selected sample identities/order to remain fixed, and the audit to reject a changed scenario result or ammo-scope overclaim. This is not a live behavior or operational-threshold decision.

**C.** The source run predates current V39 and did not execute this controller. Threshold pairs are a declared scenario grid, not the old run's authored policy. Only ten selected manual HUD values are available here, with large gaps; the separate pixel replay sampled 60 frames but did not produce OCR/numeric health for each. Any observed crossing is only the first retained selected sample below floor, not its continuous onset. Coarse samples at 56.2 and 56.4 bracket the observed pending/return boundary.

**U.** No paired dense ammo values are available; ammo guard behavior is explicitly not replayed. No exact health-guard invalidation time, interruption latency, input release, stale-answer discard, useful feedback, recovery, causal threat response, survival, MAP01 completion, or threshold adequacy follows. Live Issue #59 allocation remains separately unassigned and unauthorized.

## Initial process output (not a scientific result)

The deterministic replay covers 12 hypothetical threshold pairs. With a hard minimum of 100, the first selected below-floor sample is 47.0 while the old video labels local cover and model thinking. With a floor of 95, the first selected crossing is 54.8, also during the pending-labelled interval. With a floor of 90, the first selected sample below it is 56.4, after the last pending-labelled sample at 56.2. With a floor of 80, none of the selected samples crosses it. These are descriptive threshold scenarios only. Because the historical controller is not V39 and the thresholds were not in force in that run, this does not show that V39 would have interrupted, nor that any threshold is appropriate.

The useful conclusion is a measurement gap: current live qualification must retain paired typed health/ammo observations, the exact admitted guard receipt/floor, invalidation event, planner cancellation/terminal, verified empty release, and independent useful-outcome onset on one clock. Selected HUD screenshots cannot substitute for that chain.

## Reproduction

Run `candidate.py fixture.json result.json`, followed by `audit.py fixture.json result.json`, and `python -m unittest -v test_replay.py` inside the image and resource profile frozen in `FREEZE.json`. `RUN_RECORD.json` preserves the exact commands, outputs, hashes, and container invocation counts.
