# V39 ammo completed-future drain A08

This one-shot synthetic probe checks the completed-future boundary introduced in the latest frozen main controller. It feeds an actual paired health/ammo monitor a queued observation after a deterministic planner future is completed, drains the paired observation and completed empty terminal, and runs the frozen final-admission helpers.

H: If the bounded drain runs before `future.result()`, ammo 1 remains eligible only for fresh action-validity evaluation, while ammo 0 produces `ammo:below_hard_minimum` and final admission rejects the still-answer-eligible planner response.

T: The candidate checks the exact frozen main AST ordering and executes the frozen controller helper slices with deterministic queue/client fakes. It ran once after freezing source identities. The independent auditor binds `events.jsonl` to embedded events and has mutation tests for duplicated cases, event divergence, invalidation, admission, and terminal release.

D: `PASS_CONSTRUCTION_RACE` for the exact completed-future drain path when both cases meet the outcomes and no input authority is admitted.

C: The queue drain could miss paired evidence or fail to propagate hard invalidation into final admission; the terminal could lack verified empty release.

U: Synthetic values and deterministic fakes do not establish live race frequency, HUD cadence, physical release, action usefulness, recovery, or game success. No model, game, GUI, OS input, or live allocation was used. This does not test the pending-future cancellation path, covered separately by A06.

Frozen main: `48496b645b1cbf4c4ddea49315972724f020343c`.
