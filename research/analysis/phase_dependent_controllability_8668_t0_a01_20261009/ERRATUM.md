# Issue #8668 T0 A01 — post-run audit erratum

## Disposition

**`FAIL_HARNESS`; the former `PASS_METHOD_SCOPED` disposition and static-policy contrasts are withdrawn.** Keep the original `REPORT.md`, frozen source, first candidate output, and first audit byte-for-byte as the historical first outcome. This erratum supersedes their interpretation; it does not rewrite or replace that evidence. No candidate rerun was performed.

## Reproducible inconsistency

A read-only consistency check of the retained 481-row candidate output found 228 rows in which `actual.removal_confirmed_before_emit` is `true` while `policies.STATIC_UNCONTROLLABLE.safe_cancel_missed` is also `true`. In the example `proposed-0-0-control_first-effect_first-none-no-retry`, the plant trace contains `CANCEL_REMOVAL_CONFIRMED(op1)`, but the policy record says the globally-uncontrollable policy missed that safe cancellation.

The candidate computes the canceled plant outcome before branching over policies. It therefore reuses the phase-aware cancellation outcome for the `STATIC_UNCONTROLLABLE` comparator, even though that policy emits no cancellation. That comparator needs its own counterfactual outcome on the same exogenous schedule: without the cancellation, the original operation proceeds according to the frozen plant. The raw-only auditor repeats the candidate's shared mapping, so its zero-error result and five mutation controls do not detect this policy-counterfactual error.

This invalidates the reported static-policy contrast and the gate that depended on it. It does not determine whether phase refinement is useful under a corrected comparison, and it says nothing about a real GUI/backend. See the [Issue #8668 consistency finding](https://github.com/Unjuno/agent-interface/issues/8668#issuecomment-6067281161) and the [PR correction notice](https://github.com/Unjuno/agent-interface/pull/8698#issuecomment-6067323818).

## Next valid test

A successor needs a new allocation and freeze. Each policy must independently apply its own control action to the same exogenous schedule; specifically, the no-cancel comparator must let the original operation proceed. A separately implemented oracle must reconstruct those per-policy plant outcomes from the retained candidate rows and reject a mutation that substitutes another policy's outcome. Preserve this failed first outcome unchanged. Do not infer a runtime defect or GUI safety property from the finite model.
