# Predicate-aware GUI history reduction

This family connects predicate-based target membership with bounded schedule reduction. The three questions are related but distinct: #8592 reduces typed lifecycle schedules, #8613 detects predicate-membership phantoms, and #8663 tests their combination in a finite synthetic history model. None establishes a real backend's completeness or atomicity.

## #8592: bounded DPOR for typed lifecycle schedules

- **Status:** closed at its stated finite-method scope.
- **Outcome:** Merged [PR #8602](https://github.com/Unjuno/agent-interface/pull/8602) reports `PASS_DPOR_METHOD_SCOPED`: the independent audit matched 45,360 exhaustive schedules against 217 DPOR representatives for its frozen lifecycle model. Earlier execution STOPs and a superseded preformal freeze remain separate preserved records. This does not establish runtime speed or live safety.

## #8613: predicate-membership phantom detection

- **Status:** the finite A01 study is complete; Issue #8613 is being closed at that scope. Evidence is preserved by [PR #9725](https://github.com/Unjuno/agent-interface/pull/9725), and original PR #8627 is superseded. A separate saved-row reconstruction in [PR #9727](https://github.com/Unjuno/agent-interface/pull/9727) reproduced the aggregate safety counts under the same finite model; it is not nonauthor human review. Real-backend applicability remains unverified and is retained below as a research idea.
- **Outcome:** [PR #8627](https://github.com/Unjuno/agent-interface/pull/8627) records one candidate and one independent raw-only audit over 77,700 ordered deterministic histories; 9/9 copied-evidence corruptions were rejected. The independent oracle counted 1,277 safe unique outcomes. `NODE_ONLY` admitted 14,742 outcomes including 13,465 oracle-unsafe admissions; `ALWAYS_REQUERY` admitted 2,543 including 1,266 unsafe; `MEMBERSHIP_CERT` admitted 1,277 with zero unsafe admissions and zero safe false refusals. The result is `PASS_PHANTOM_DETECTED_SCOPED`, using a supplied private Linux/CPython environment without Docker/WSLc image attestation. The certificate assumes complete enumeration of matching-member, completeness and scope changes; it is not production-ready and cannot grant authority.

## #8663: predicate-aware DPOR

- **Status:** open for the distinct runtime question. The evidence is preserved on main by [PR #9723](https://github.com/Unjuno/agent-interface/pull/9723), with navigation in [#9724](https://github.com/Unjuno/agent-interface/pull/9724); original PR #8692 is closed as superseded.
- **Outcome:** The frozen candidate matched exhaustive outcomes across 14 synthetic fixtures and reduced 1,719 schedules to 217 representatives; the unrelated-event control reduced 840 to 1. Audit v1 stopped on a prefix-replay bug, v2 failed on ordering/mutant handling, and audit v3 passed 2,973 checks while verifying that three underdependent mutants miss oracle outcomes. The candidate was not rerun, but the preregistered single-auditor count was exceeded by the versioned audit attempts. The corrected v3 result remains protocol-deviating and does not satisfy the original one-auditor gate. Preserve it together with the STOP, FAIL and deviation; evidence integration is custody, not a clean formal PASS. No GUI, runtime-adapter completeness, authorization, latency or product result follows.

## Boundary

The finite models establish only their own declared transition and predicate semantics. The future #8613 transfer question is whether a real backend can establish complete, atomic and historically coherent target-set observations through admission. Compare against existing coarse scope invalidation and endpoint requery under matched tasks; preserve unknown and transient changes, independently score task effects and cost, and freeze a new protocol before any live experiment. The current scoped result does not answer that question. Any future runtime claim would require evidence that an actual adapter enumerates a complete and atomic predicate scope and respects source freshness, authority and effect gates. This record does not authorize live probing or another allocation.
