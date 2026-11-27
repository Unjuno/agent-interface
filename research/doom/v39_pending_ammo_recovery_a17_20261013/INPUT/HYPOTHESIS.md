# A17 pending-turn ammo recovery

**H:** When source ammo is 4 and an eligible action requires 6, a newer same-binding observation at ammo 6 arriving while the persistent planner is pending should allow that same synthetic answer to reach `READY_FOR_FRESH_EXECUTOR_ADMISSION`; an unchanged-current-4 control should reject it as `ammo_minimum_failed`. Neither arm may grant executor or input authority.

**T:** Exercise the real frozen `PersistentPlannerAdapter` with deterministic fake completion, then the exact frozen current-main V39 final-admission path. Run one WSLc single-container CPU candidate from the frozen image.

**D:** PASS only if sequence 11/current ammo 6 passes the authored minimum 6, while current ammo 4 fails; both results remain executor-admission null and input-authority false.

**C:** This is a deterministic predicate-path test; it does not establish tactical correctness of the threshold or source observations.

**U:** Fake client, synthetic response, typed observations. No model inference, live game, GUI/OS input, physical release, recovery, task effect, or live allocation. Construction evidence only.
