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
the follow-up horizon is not fully observed and observed candidates are
well-formed, and reports any candidate follow-up with a missing or non-boolean
discard flag as invalid auditor input. It intentionally does not claim plan
admission; correlate each proposed recovery with the independent admission and
cancellation-custody receipts before assigning the preregistered scoped PASS.

Eight strict-classifier tests passed under CPython 3.11.9 in normal and
optimized (`python -O`) mode. They cover the production hard-guard shape,
missing and null flags, missing flags across a complete follow-up horizon,
explicit discarded plans, explicit non-discarded fresh plans, right censoring,
duplicate iterations, the preserved-test import alias, and cap violations.
The test constructs a counterexample where the frozen predicate labels
malformed evidence as recovery while the strict classifier does not. Full
package discovery also passes 11/11 in both modes, including the three
byte-preserved frozen tests.

## Applicability to the A16 outcome

The retained A16 result reports zero authored-cover hard-health guard
exposures and no `episode/report.json`; it is an allocation-level STOP after
death, with health zero rejected at the subsequent source refresh. Therefore
the permissive recovery predicate did not classify or cause A16's STOP. This
review protects interpretation of a future exposed-guard run; it does not
reclassify A16.

The selected trace excerpt shows decision 11 received health 4 and proposed
`critical_health_minimum = 1`, `maximum_health_loss = 3`; the next typed sample
was health zero. This establishes the observed boundary and the failure to
finish MAP01, but does not establish that a higher floor would have prevented
death. A discriminating next live test must expose a hard guard while health
is still in the supported positive domain and retain the ordering of guard,
cancellation/release, and any fresh follow-up plan. It needs a distinct,
pre-registered allocation and confirmed lane availability.

The separately frozen A17 package at commit
`defe7f0d1ec8ea3716cc64b92f79720aa7a01c92` uses the same permissive recovery
predicate and a positive test fixture with the discard field omitted. A static
check of its exact base controller found that all seven decision-row creation
paths include a boolean `model_action_discarded` field; this does not show that
an eventual well-formed A17 report would be misclassified. It does show that
the A17 auditor lacks a fail-closed check for malformed/missing follow-up
fields. The strict classifier can serve as an additive post-run check on a
retained A17 report without changing its freeze or allocation.

## Disposition

This is a method review and independent post-run check, not live-control or
task-effect evidence. The frozen allocation, source, raw records, and initial
audits remain immutable. Use this classifier only as an additive sensitivity
check; any changed preregistration or live treatment requires a new allocation.
