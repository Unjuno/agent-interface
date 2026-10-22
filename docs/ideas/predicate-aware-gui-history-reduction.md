# Predicate-aware GUI history reduction

This family connects predicate-based target membership with bounded schedule reduction. The three questions are related but distinct: #8592 reduces typed lifecycle schedules, #8613 detects predicate-membership phantoms, and #8663 tests their combination in a finite synthetic history model. None establishes a real backend's completeness or atomicity.

## #8592: bounded DPOR for typed lifecycle schedules

- **Status:** closed at its stated finite-method scope.
- **Outcome:** Merged [PR #8602](https://github.com/Unjuno/agent-interface/pull/8602) reports `PASS_DPOR_METHOD_SCOPED`: the independent audit matched 45,360 exhaustive schedules against 217 DPOR representatives for its frozen lifecycle model. Earlier execution STOPs and a superseded preformal freeze remain separate preserved records. This does not establish runtime speed or live safety.

## #8613: predicate-membership phantom detection

- **Status:** open; A01 reports a finite synthetic method PASS; evidence PR remains Draft.
- **Outcome:** [PR #8627](https://github.com/Unjuno/agent-interface/pull/8627) records one candidate and one independent raw-only audit over 77,700 ordered deterministic histories; 9/9 copied-evidence corruptions were rejected. The independent oracle counted 1,277 safe unique outcomes. `NODE_ONLY` admitted 14,742 outcomes including 13,465 oracle-unsafe admissions; `ALWAYS_REQUERY` admitted 2,543 including 1,266 unsafe; `MEMBERSHIP_CERT` admitted 1,277 with zero unsafe admissions and zero safe false refusals. The result is `PASS_PHANTOM_DETECTED_SCOPED`, using a supplied private Linux/CPython environment without Docker/WSLc image attestation. The certificate assumes complete enumeration of matching-member, completeness and scope changes; it is not production-ready and cannot grant authority.

## #8663: predicate-aware DPOR

- **Status:** open; evidence PR [#8692](https://github.com/Unjuno/agent-interface/pull/8692) remains Draft.
- **Outcome:** The frozen candidate matched exhaustive outcomes across 14 synthetic fixtures and reduced 1,719 schedules to 217 representatives; the unrelated-event control reduced 840 to 1. Audit v1 stopped on a prefix-replay bug, v2 failed on ordering/mutant handling, and audit v3 passed 2,973 checks while verifying that three underdependent mutants miss oracle outcomes. The candidate was not rerun, but the preregistered single-auditor count was exceeded by the versioned audit attempts. Preserve that process deviation alongside the reported `PASS_DPOR_PREDICATE_SCOPED`; the evidence remains in an open Draft PR, not integrated. No GUI, runtime-adapter completeness, authorization, latency or product result follows.

## Boundary

The finite models establish only their own declared transition and predicate semantics. Any future runtime claim would require evidence that an actual adapter enumerates a complete and atomic predicate scope and respects source freshness, authority and effect gates. This record does not authorize live probing or another allocation.
