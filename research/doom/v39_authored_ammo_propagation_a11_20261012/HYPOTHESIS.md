# A11 — authored ammunition threshold propagation

Freeze time: 2026-10-12 before the WSLc test. Current main is `f185a9059d485a4f8d5a65e9e7f6782897f67eae`; exact controller, guard, action-contract, and action-admission source identities are in `FREEZE.json`.

**H:** The current action-admission contract will reject a fire action when an authored minimum-ammo predicate of 5 is crossed from 6 to 4, while the current paired V39 cover monitor will preserve its fire cover because its separate ammo hard floor is 1. Both paths should invalidate at zero ammo.

**T:** Invoke the actual current-main `build_cover_monitor` with a fire cover and same-epoch health/ammo readers; use the actual `doom_action_validity_contract_v1.build_contract` and `action_validity_admission_v1.evaluate_action_validity` for the same source epoch and authored action bound. Compare current ammo 4 under source ammo 6, then run zero ammo as a monitor boundary control. Extract exact controller definitions only; use the real `ObservableSignalGuard`. Run once in WSLc with networking disabled, one CPU requested, 512 MiB requested.

**D:** PASS_SCOPED requires the action boundary to reject ammo 4 with `ammo_minimum_failed`, the cover monitor not to invalidate at ammo 4 while reporting hard floor 1, and the monitor to invalidate at ammo 0. Input identity mismatch is HOLD; any different pattern is FAIL_SCOPED.

**C:** The planner's action minimum and local cover's positive ammo floor may be deliberately distinct policy contracts. A component-boundary discrepancy does not by itself prove the controller violates the intended live cover policy or that the minimum must be propagated.

**U:** Synthetic HUD values only. No pending planner wait, cancel loop, game, OCR, GUI, physical input, release, feedback, recovery, ammo consumption, progress, task effect, terminal outcome, or live allocation was tested. This is not a claim of end-to-end control failure or success.
