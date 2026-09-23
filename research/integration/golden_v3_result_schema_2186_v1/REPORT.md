# Golden v3 result schema freeze (#2186)

## Result

**PASS_GOLDEN_V3_RESULT_SCHEMA_FREEZE_SCOPED**

A new additive schema `golden-v3-result-v1` freezes nine lifecycle states: doctor, model attempt, observation, guarded dispatch, refusal, effect, repair, release, and cleanup. Five representative fixtures were accepted: success, partial effect, refusal, stale invalidation, and cleanup failure. A deliberately contradictory cleanup-failure-as-success fixture was rejected.

The schema keeps `task_success` distinct from `program_completed`, retains `partial_effects`, forces cleanup failure to `cleanup_failed` with `task_success=false`, and fixes `authority_granted=false`.

Container result: `python:3.12-slim`, py_compile plus one validator run.
Digest: `9dd137c429972b3e09a7f21c93b7bf15a0e86994e10c48aacae8f8756505ebf4`.
Counters: accepted=5, model=0, GUI=0, input=0.

## Boundary

This freezes a research integration contract only. It does not modify runtime, implement the adapter, run GUI/model/input, or establish desktop task correctness, latency, or product readiness. The schema is the prerequisite for a future adapter successor.
