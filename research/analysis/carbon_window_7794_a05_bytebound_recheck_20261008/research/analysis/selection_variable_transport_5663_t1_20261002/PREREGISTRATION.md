# Issue 5663 T1 preregistration

## H — hypothesis
In the frozen two-domain finite control, explicit stratum support and within-stratum route-effect checks distinguish composition shift from mechanism shift: reweighting source conditional effects recovers the target effect in the composition-only scenario, while a changed conditional effect, missing support, or endpoint mismatch refuses a transport result.

## T — test
One deterministic finite method-control allocation, no random sampling. Contrast interface route B with plain route A for binary success in two strata, easy and hard. Source population weights are 90/10 and target weights 10/90. In the stable-effect control, per-stratum B−A effects are +0.04 and −0.10 in both domains: the source aggregate is +0.026, target direct aggregate is −0.086, and target-standardized source effect is −0.086. A mechanism-shift countercontrol changes target conditional effects to +0.12 and −0.02; its target-direct effect is −0.006 while the naive source-standardized diagnostic remains −0.086 and must not be published as a transport estimate. Two controls remove source support for a target-relevant stratum and change the task endpoint contract. Candidate and raw-only auditor are separate programs. Four frozen scenarios, exact integer outcome counts, no model/GUI/GPU/input/network. The formal package is to run once in one WSLc candidate container then one separate CPU-only WSLc audit container; retries=0. Construction tests are distinct.

## D — decision
METHOD_PASS_SCOPED only if an independent auditor reconstructs all four cases; the composition-only case yields source +0.026, target −0.086, standardized −0.086; the mechanism-shift case yields target −0.006 but no transport estimate; missing support yields HOLD_NONTRANSPORTABLE; endpoint mismatch yields HOLD_NONCOMPARABLE; and frozen sign/hold corruption controls are rejected. Any discrepancy is FAIL_METHOD or FAIL_AUDIT. This controls the arithmetic/decision method only; it does not qualify any actual fixture result for transport.

## C — competing explanations
An apparent sign reversal could come from changed conditional route effects rather than stratum composition. In real applications, endpoint/scorer mismatch can mimic effect change; finite binary cohorts can also vary by chance. A direct target measurement may be preferable to transport modeling.

## U — uncertainty and exclusions
The rows are exact stipulated finite counts, not sampled GUI tasks. The source/target endpoint and stratum are defined by construction. No hidden effect modifiers, model output, user population, latency, tokens, application effects, safety/collateral, causal identification, platform transfer, or deployment claim is tested. METHOD_PASS_SCOPED must not be upgraded to TRANSPORT_SCOPED.

## Frozen base and identity
Allocation SELECTION-TRANSPORT-5663-T1-20261002-01, seed label 5663001 (deterministic fixture, no RNG). Main SHA at work start: 67ebd3016af9ed99a5cb40a39d4d753871f51d75. Formal execution is pending shared WSLc ownership arbitration; no candidate invocation is authorized or claimed by this preparation record.