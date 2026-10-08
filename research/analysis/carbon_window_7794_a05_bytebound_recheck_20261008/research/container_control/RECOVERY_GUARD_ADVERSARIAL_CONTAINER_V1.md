# Bounded recovery guard adversarial container study v1

Status: **CONTAINER COUNTEREXAMPLE FOUND; DEADBAND REPAIR CANDIDATE RETAINED. NO MAP01 EFFICACY CLAIM.**

Repository context observed before publication: `ff2bbb5e200e2bf8ee2295ad97ca9dd0f158a371` on `main`.

## Question

The retained container/X11 v3 mechanics result showed that source-bound bounded recovery can reduce unsafe exposure relative to coast in one rendered tracking fixture, and the real MAP01 development transfer showed that recovery can reduce measured no-input planner-wait while preserving release/scorer invariants. The remaining risk is policy-side: can a guard that checks only action direction plus bounded source displacement still admit a locally harmful continuation?

This study searches specifically for that counterexample in a disposable, network-independent Python container model before another live allocation.

## Model boundary

This is a deliberately simplified one-dimensional control stress model. It does not simulate DOOM semantics, X11 timing, model quality, ViZDoom, or a deployable recovery policy. It is used only to falsify overly weak guard logic.

Each matched episode has a 600 ms planner wait, 10 ms integration cadence, source state inside the nominal safe region, a previous action aimed toward source-frame center, exogenous drift that may reverse once, observation noise, a coast arm with no input, and a recovery arm that may reuse the previous action while its guard remains valid. Exact state is used only by the offline scorer.

The first guard requires only that the observed sign still agrees with the prior action direction and observed displacement from the source remains below a fixed bound.

## Experiment 1 — adversarial sweep

Executed in the container:

- 240 parameter conditions;
- 1,200 matched episodes per condition;
- 288,000 matched episodes total;
- recovery budgets: 80, 160, 240, 320, 400 ms;
- observation noise: 0, 0.01, 0.03, 0.06 normalized units;
- drift-switch probability: 0, 0.15, 0.35, 0.60;
- source displacement guard: 0.08, 0.16, 0.24.

A counterexample was found. One high-worse-rate condition used budget 240 ms, observation noise 0.01, no drift reversal, and source displacement guard 0.16. Recovery was worse than coast in **8.33%** of 1,200 matched episodes, while instantaneous locally harmful recovery occurred in **15.67%**. The mean unsafe-time difference still favored recovery by about 110 ms.

The important result is therefore not the favorable mean. A guard can improve the average while still admitting a nontrivial harmful tail. The model failure is center overshoot: an action that was directionally correct at the source can remain sign-consistent but become unnecessary close to the target, where another pulse moves the state farther from center than coast would.

## Experiment 2 — deadband repair sweep

A second independent container script added one condition only: recovery is cancelled when the observed state enters a target deadband. Source-displacement and direction checks remain.

Executed:

- 320 parameter conditions;
- 700 matched episodes per condition;
- 224,000 matched episodes total;
- budgets: 80, 160, 240, 320 ms;
- noise: 0, 0.01, 0.03, 0.06;
- drift-switch probability: 0, 0.15, 0.35, 0.60;
- fixed displacement guard 0.16;
- deadband: 0, 0.03, 0.06, 0.10, 0.14.

Within this synthetic model, many deadband configurations removed the observed harmful tail. Examples across all four drift-switch probabilities:

| budget | noise | deadband | max recovery-worse rate | max harmful-episode rate | worst mean unsafe delta |
|---:|---:|---:|---:|---:|---:|
| 320 ms | 0.01 | 0.06 | 0 | 0 | -67.96 ms |
| 320 ms | 0.00 | 0.06 | 0 | 0 | -65.19 ms |
| 240 ms | 0.01 | 0.06 | 0 | 0 | -60.29 ms |
| 240 ms | 0.03 | 0.10 | 0 | 0 | -57.91 ms |

These zeros are finite-sample observations in a simplified simulator, not safety guarantees.

## Interpretation

**The previous action's direction and source displacement are insufficient guard semantics by themselves.** A bounded recovery policy also needs a task-relative termination/postcondition region, or an equivalent projected-benefit test, so that valid old authority does not imply useful continued actuation.

Authorization lifetime and action usefulness are separate properties. A source-bound lease may still be fresh while its motor continuation has become locally counterproductive.

The smallest next test is not to increase the recovery lease. Add a task-relative stop/deadband/postcondition to the rendered container/X11 mechanics fixture, expose at least one natural center-entry cancellation, and verify that it preserves the existing no-stale-repress and empty-release gates. Only after that should the same semantic condition be considered for a new MAP01 formal version.

## H / T / D / C / U

**H — falsifiable hypothesis.** Direction + source-displacement guard alone can admit a continuation that is worse than coast after task state enters a region where the prior action is no longer useful.

**T — minimum test.** Sweep matched coast/recovery episodes across recovery budget, observation noise, exogenous regime change and displacement guard. Then repeat with a target deadband while preserving all other synthetic dynamics.

**D — disposition.** **PASS counterexample; candidate repair only.** The weak guard is falsified in the stress model. Deadband eliminates the observed harmful tail in many finite sampled conditions but is not promoted without rendered/X11 and domain transfer tests.

**C — competing explanations.** The overshoot may be an artifact of this 1-D model; real tasks may have inertia, asymmetric effects, richer postconditions, or no meaningful center target. Conversely, real visual noise and delayed effects may make the failure worse.

**U — uncertainty.** Model mismatch dominates. The sweep does not estimate MAP01 failure probability, X11 release latency, human tempo, model latency, or general GUI correctness.

## Container provenance

Executed scripts and retained summary are hash-bound:

- `recovery_stress_v1.py` SHA-256 `6067529e812f6348dc25212756d91aad9001f28d51edc2fadd5d1308afd31eb1`;
- `recovery_deadband_stress_v1.py` SHA-256 `488fd7eeeb08d3f3d7b252a82046b69cd77e838dbc54b0edc520eb7a0b0f651a`;
- full stress JSON SHA-256 `ced529209d7844e64add2b8ba26c1aac4993f8f8b59dc1a4221cf5ba7f8e6007`;
- full deadband JSON SHA-256 `2913eb66902c2602cf73895037d193041457e3825755de67ccf66c84e7f7c049`;
- retained summary SHA-256 `0e68a06208bd7dcaca3819eefb930600b037c54bb1a25892ba46e50183c86672`.

The large per-condition JSON files are not required for the repository claim; the scripts deterministically regenerate them from the frozen seeds.
