# MAP01 visual generalization container study v1

Status: **NEGATIVE GENERALIZATION RESULT; SCREEN-ONLY CONTINUOUS PLANNER FOLLOW-UP IN PROGRESS.**

Base observed before publication: `ea182d26755621a1a25dbaaac3a2d5f5dc74f3b2`.

This lane is independent of the formal MAP01 timing/release allocations. It changes no shared runtime, workflow, retained formal result, authority semantics, scorer contract, or release path. All experiments here were executed in the disposable Linux container with the bundled ViZDoom/Freedoom runtime before publication.

## Question

Can normal-combat strict-clear demonstrations be converted into a screen-only MAP01 controller that transfers to unseen seeds, without exposing live position, angle, health, ammo, route phase, or privileged scorer state to the deployed controller?

The broader goal is not a MAP01 coordinate script. The candidate mechanism should transfer to ordinary computer interaction: short reusable programs, visual re-localization, effect checking and narrow deoptimization instead of long open-loop replay.

## New teacher coverage

The unchanged continuous privileged teacher from the earlier construction was run on a new, disjoint seed block `993000..993019` with normal combat, no `god`, no `notarget`, no save/load and a strict timeout-aware completion test.

Five of twenty runs were strict clears:

- `993005`
- `993012`
- `993014`
- `993016`
- `993017`

The five successful runs contribute 2,215 action-before frames. Combined with the six previously retained local strict-clear demonstrations, the experimental memory contains 11 normal-combat successful trajectories and 4,462 screen/action records. Teacher coordinates are used only to generate the demonstrations; the evaluated runtime policies below do not receive live pose.

This teacher success rate is not a deployment claim.

## Memory coverage ablation

The previously explored topological-contrastive screen controller was rerun without algorithm changes, replacing the six-success memory with all eleven successes. Twenty-four unseen seeds `993100..993123` were evaluated.

Result:

- strict clear: **0/24**;
- deaths: **0/24**;
- median topological state index: **3**;
- maximum state index: **9**;
- dominant stop: `contrastive_repair_failed` (**17/24**).

Therefore the prior 1/12 screen-only strict clear does not become reliable merely by adding more successful trajectories. The failure is not explained by six-demo memory sparsity alone.

## Structural descriptor ablation

A low-frequency grayscale structural descriptor was substituted for HOG while keeping the topological/deoptimization logic fixed. Offline leave-one-success landmark recognition reached 93.6% top-1 and 99.1% top-2 over the ten selected landmarks.

On 24 new runtime seeds `993200..993223`:

- strict clear: **0/24**;
- deaths: **2/24**;
- median state index: **4.5**;
- maximum state index: **5**.

The structural representation improves descriptive depth but does not solve transfer.

## Held-out source-of-error probe

Eight additional seeds `993300..993307` were run only as privileged teacher/evaluator probes. Their true route phase is used for diagnosis, not controller input.

Across 710 normal-combat frames tagged with the ten landmark phases:

- HOG global phase recognition: **72.25% top-1**, **80.85% top-2**;
- low-frequency blur: **62.54% top-1**, **72.39% top-2**;
- border-only low-frequency descriptor: **61.97% top-1**, **70.28% top-2**.

A second disjoint eight-seed probe `993320..993327` records the teacher's actual local action at the same landmark phases. If the correct phase is supplied to retrieval, nearest successful HOG memory still predicts the exact local action only **74.21%** of the time. When the action label matches, retained duration is stable: mean absolute duration error is about **0.08 tic**.

Thus two errors remain distinct:

1. long-horizon place/phase recognition is imperfect;
2. even under the correct phase, approximately one quarter of local action choices do not transfer by nearest-memory lookup.

The bottleneck is not action duration calibration.

## Alternatives tested and rejected

### Markov action prior

A phase-local image-memory action selector was augmented with the previous action as a transition prior. Lambda was selected only by leave-one-success-seed cross-validation. Training CV improved from 67.7% at zero prior to 74.4% at the selected `lambda=0.1`; the frozen held-out probe remained **74.44%** exact. No transfer improvement is observed.

### Phase-conditioned CNN

A small CNN conditioned on the expected topological phase was trained on the eleven successful trajectories. Its frozen held-out action result was only **42.57% exact / 44.03% coarse**, substantially below HOG retrieval. Reject.

### Derivative-free visual servo

A controller probed short left/right/forward/back/strafe actions and retained a probe only when the contrastive expected-landmark objective improved. Twelve unseen seeds `993400..993411` yielded **0/12 strict clear**, two deaths, median state index 3.5 and maximum 9. Reject the current objective/servo pairing.

### Active stabilization before recognition

A bounded screen-change gate attempted to suppress active threats before landmark classification. On twelve unseen seeds `993700..993711`, all twelve stopped at state index 1 with `contrastive_repair_failed`. Animated/non-semantic changes caused unnecessary suppression motion. Reject this scalar frame-change gate.

## Interpretation

The retained evidence rejects four attractive shortcuts:

- adding more successful demonstrations alone;
- replacing HOG with a smoother static descriptor alone;
- adding a simple action-sequence prior;
- optimizing a scalar visual-landmark distance by local probes.

The common failure is **semantic aliasing plus local action ambiguity**. A screen can look compatible with a route state while the controller is in a different interaction/motion context. Conversely, the correct route phase does not uniquely determine the next motor action from a single image.

For Agent Interface this maps directly to GUI control: visual similarity must not itself authorize replay. Reuse needs action/effect history and a task-relative progress condition, while deoptimization must preserve the last verified semantic state.

## Separate continuous screen-only planner experiment

A persistent ViZDoom process has also been created in the container for a distinct direct test. The command interface exposes only current pixels and terminal status to the planner. Live pose, angle, health, ammo and scorer fields are omitted from the planner interface and retained only for post-run audit.

The current run uses learned successful local programs as bounded skills and an external strong visual planner to inspect the screen at skill boundaries and repair visible failures. This run is not yet terminal and is therefore **not** counted as success or failure in this report.

## H / T / D / C / U

### H — falsifiable hypothesis

Increasing successful memory coverage and/or using a more structure-biased visual representation is sufficient for the existing topological-contrastive controller to produce repeatable screen-only strict MAP01 clears on unseen seeds.

### T — minimum test

Use disjoint teacher-success and runtime seed sets. Keep runtime authority screen-only. Evaluate at least 24 unseen seeds for the memory-coverage and representation ablations, and separately diagnose recognition and local-action transfer on disjoint teacher/evaluator probes.

### D — disposition

**FAIL for the hypothesis.**

Neither 11-demo memory nor the structural descriptor produced a strict clear in their 24-seed blocks. Diagnostic probes show both place recognition and local-action selection errors remain material.

### C — competing explanations

- The ten-landmark abstraction may be too coarse.
- Correct progress may require short temporal/action-effect context rather than one frame.
- Combat dynamics can make an otherwise correct navigation action locally inappropriate.
- Successful teacher trajectories may cover too narrow a state tube even when their seed count grows.
- The local repair objective may contain visual local minima unrelated to semantic task progress.

### U — uncertainty

The study is one MAP and one game family, uses teacher-generated successes, and does not establish a lower bound on what a frontier visual planner can accomplish. It also does not rule out learned temporal state estimators, richer effect receipts, explicit uncertainty sets, or interactive active perception. No human-tempo or general GUI claim follows.

## Next gate

Do not tune the failed scalar landmark thresholds further. The next high-information choices are:

1. finish and audit the persistent screen-only strong-planner run;
2. test short **action-effect histories** as the retrieval key rather than a single screenshot;
3. require semantic progress/effect evidence before a reused local program advances the topological state;
4. transfer any winning mechanism to a normal GUI fixture before promotion.
