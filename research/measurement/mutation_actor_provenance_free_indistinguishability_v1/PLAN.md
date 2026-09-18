# #1579 Provenance-free actor indistinguishability

TASK: MUTATION-ACTOR-PROVENANCE-FREE-INDISTINGUISHABILITY-20260918-001
PARENT: #47

## H
When HUMAN and EXTERNAL_PROCESS histories have byte-identical verifier-visible event/effect/timing state and no trusted actor witness, deterministic actor-specific classification cannot be correct for both members of the pair. Safe fallback is UNATTRIBUTED.

## T
Analytical proof plus complete finite enumeration over 384 observable states and two hidden producers. Representative deterministic heuristics are evaluated on the same paired corpus. Trusted-witness controls add exactly one discriminating field.

## D
PASS only if all 384 provenance-free pairs are observable-identical, every actor-specific heuristic has at least one error per pair, UNATTRIBUTED makes zero false specific claims, trusted bound witnesses separate every control pair, and audit/integrity passes.

## C
Trusted kernel/device/broker/hardware provenance can break the equivalence; timing/pixels/event shape alone cannot in this declared model.

## U
Analytical contract boundary only; no claim about availability/reliability/privacy of real provenance sources.
