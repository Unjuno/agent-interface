# Issue #7466 — A03 conservative online-evidence gate

## H / T / D / C / U

**H.** A calibrated observable risk signal should not activate adaptive checkpoint placement solely because it predicted well on training/validation traces. Requiring fresh within-run feedback to provide a likelihood ratio of at least 1000 after at least 128 observations, then returning to the event-boundary baseline if that evidence falls below 100, should avoid adaptations on independent/reversed signals while retaining a possible cost benefit on held-out informative traces.

**T.** Deterministic standard-library simulation, no model/GUI/input/provider. Fit signal interruption rates on 64×96 training observations; require validation Brier improvement over a constant base-rate predictor on 32×96 disjoint observations. Evaluate 24 fresh held-out episodes each for informative, independent, and reversed signal-risk relationships, with task length 300, horizon 3000, fixed interval 16, task-event interval 20, checkpoint costs `{1,4,8}`, and replay costs `{1,3}`. Every policy receives the same hidden interruption realization for an episode/cost cell. Compare fixed, task-event, sequential-evidence-gated adaptive, and auditor-only clairvoyant lower bound. Candidate receives only current public signal/state and the latest interruption feedback; oracle cohort labels and future outcomes remain unavailable to the policy.

**D.** `PASS_ADAPTIVE_PLACEMENT_SCOPED` requires exact completion/effects and zero illegal checkpoints in every row; every informative checkpoint/replay cost cell must reduce median total cost by at least 10% against both fixed and task-event baselines; and no independent or reversed trace may activate adaptation (therefore those traces must match task-event decisions exactly). Any failed correctness gate is `FAIL_UNSAFE_RESUME`; a clean audit with unmet benefit/abstention criteria is `PASS_SAFETY_NO_BENEFIT` or `FAIL_CALIBRATION` as encoded by the frozen auditor. Four mutation controls must be rejected. One candidate and one auditor invocation; no retry or post-result threshold changes.

**C.** Conservative activation may arrive too late to save enough recovery work; a high posterior-evidence threshold can abstain even when a signal is useful. Fixed/event placement may remain cheaper once checkpoint and replay costs vary. Periodic signals and planted hazards may exaggerate predictability.

**U.** Finite synthetic method evidence only. No real interruption prevalence, semantic checkpoint serialization/verification, non-idempotent effect recovery, GUI/process safety, production policy, user outcome, or runtime latency is measured. The risk process is stipulated. Host CPython is used because this protocol is a standard-library simulation and no container image is currently present locally; no pull/build or isolation claim is made.

## Why this successor differs from A02

A02 remains `STOP_PREFORMAL_SOURCE_UNFROZEN`, with formal candidate/auditor counts 0/0. Its retained construction preview showed that the policy started adaptive after global calibration and did not disable on independent-signal traces by tick 48; it also did not complete all reversed-signal episodes within its 240-tick horizon. A03 tests a new conservative, within-episode evidence-gated activation mechanism, lengthens the task/horizon to make the minimum evidence gate observable, and uses disjoint seeds. It neither repairs nor overwrites A02, and does not reuse its seed schedule.

## Reproduction

Exact base SHA, source/input hashes, runtime, invocations, and outcome are recorded in `FREEZE.json`, `RUN.md`, and `formal_01/`. Candidate and independent auditor must each run once, after `FREEZE.json` is written. Outputs are write-once; an existing output is a stop.
