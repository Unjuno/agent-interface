# A16 recovery auditor independent review

## Scope and provenance

This review examines the frozen A16 package at commit
`be5b31e2ef0d8ff02fbb07b13d4d15b92d917c19`, based on current main
`57337e95ecbecf7e762c8ec8091472b79e8ad49f`. It does not inspect or change
the live VM, consume the allocation, or alter its raw report. Frozen source
copies are retained here for reproducible local tests.

## Finding

The frozen `audit_recovery_censoring.py` counts a follow-up decision as recovery
when `fresh_sequence_at_plan` is an integer greater than the invalidation
sequence and `model_action_discarded` is anything other than the boolean
`true`. Thus a missing field, `null`, `0`, or a string can satisfy the
non-discarded condition. The predicate also does not itself require an
executor-admitted plan. The preregistered rule calls for a fresh, non-discarded
plan; independent admission evidence must therefore be checked before
interpreting recovery as an admitted reaction.

The frozen recovery unit test uses the production-recognized top-level hard
guard reason `policy_invalidation.reason = health:below_hard_minimum`; it does
execute the recovery branch. Its positive fixture omits
`model_action_discarded`, so the test explicitly codifies the permissive
missing-evidence behavior rather than detecting it. The nested
`outcomes.health = {status: HARD_INVALIDATED, reason: below_hard_minimum}`
shape is also recognized by the production helper.

The frozen `audit_live.py` duplicates the permissive predicate in its
`bounded_fresh_recovery_after_guard` calculation. `audit_a16_health_guard_result.py`
consumes the censoring counts and can emit PASS if these counts show a
recovery. No schema check for `model_action_discarded` was found in the
reviewed frozen A16 package before these computations. A16 preregistration
also requires matching cancellation and verified-empty release custody and
no stale dependent admission; these separate gates must still be independently
verified.

## Independent check

`audit_a16_recovery_strict.py` is an additive, standalone post-run classifier.
It accepts recovery only with an integer fresh sequence after the guard and
`model_action_discarded is False`. It validates unique positive decision
iterations within the declared decision cap, preserves right-censoring when
the follow-up horizon is not fully observed, and reports malformed discarded
flags as invalid auditor input when the horizon is complete. It intentionally
does not claim plan admission; correlate each proposed recovery with the
independent admission and cancellation-custody receipts before assigning the
preregistered scoped PASS.

Six tests passed under CPython 3.11.9 in normal and optimized (`python -O`)
mode. They cover the production hard-guard shape, missing and null flags,
explicit discarded plans, explicit non-discarded fresh plans, right
censoring, duplicate iterations, and cap violations. The test constructs a
counterexample where the frozen predicate labels malformed evidence as
recovery while the strict classifier does not.

## Disposition

This is a method review and independent post-run check, not live-control or
task-effect evidence. The frozen allocation, source, raw records, and initial
audits remain immutable. Use this classifier only as an additive sensitivity
check; any changed preregistration or live treatment requires a new allocation.
