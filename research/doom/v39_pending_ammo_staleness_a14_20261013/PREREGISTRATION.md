# A14 — pending-turn ammo staleness

**H:** If a persistent planner turn is started from a current observation with ammo 6 and the observation changes to ammo 4 while that turn is pending, the completed eligible answer's action must be checked against the newer same-binding observation and rejected when its authored `minimum_ammo` is 5. With no intervening ammo change (6→6), the same synthetic response should reach executor-ready status.

**T:** From exact current main, run the real `PersistentPlannerAdapter` lifecycle with a deterministic fake client whose completion callback advances a typed current observation during the pending wait; pass its `TurnResult` through the extracted current controller's `final_admission_from_planner_result` and `prepare_action_admission`. Include unchanged-ammo positive control. One WSLc single-container CPU run.

**D:** PASS for this scoped boundary if changed-current rejects with `ammo_minimum_failed`, unchanged-current reaches `READY_FOR_FRESH_EXECUTOR_ADMISSION`, and neither case itself admits executor input or grants authority. Any stale-source pass, missing binding, wrong status or unexpected authority is FAIL.

**C:** A result may be caused by the deterministic authored minimum predicate and helper composition, not any model behavior, game semantics, or live sensor reliability.

**U:** Fake client, synthetic response and typed observations. No model inference, game, GUI, OS input, physical release, recovery, progress, or live allocation. This is construction evidence only.

Base: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
