# Semantic truth maintenance — Issue #4259 first rung

Allocation: `semantic-truth-maintenance-4259-20260923-01`.

## H
An explicit support graph can preserve the exact three-valued derived-fact lattice while recomputing strictly fewer derived facts than global invalidation over the frozen mutation schedule.

## T
Standard-library deterministic fixture only. Eight base facts, six derived facts, TRUE/FALSE/UNKNOWN logic and two policies: `GLOBAL_INVALIDATE` and `SUPPORT_SET_RETRACTION`. The 14-step frozen schedule includes initialization plus unrelated mutation, support invalidation, UNKNOWN support, alternate support, producer generation reset, restoration, focus unknown/restore, submit disable/restore and document disable/restore. One formal invocation after public source/hash freeze; no retry/replacement/tuning.

## D
`PASS_SEMANTIC_TRUTH_MAINTENANCE_SCOPED` requires: exact oracle lattice and final macro-readiness equality at every step for both policies; zero unsupported retained derived facts; correct generation-reset UNKNOWN propagation; alternate support preserves `can_submit`; unrelated mutation causes zero support-policy derived recomputation; exact provenance/support-chain reconstruction; and support-policy total recomputations strictly less than global invalidation. Independent auditor errors must be empty and at least 10 coherent evidence corruptions must reject.

Contrary complete semantic result => `FAIL_UNSUPPORTED_FACT_RETENTION` or `FAIL_RETRACTION_PROPAGATION`; equal/higher recomputation => `HOLD_NO_INCREMENTAL_VALUE`; incomplete provenance => `STOP_PROVENANCE_INCOMPLETE`.

## C
All dependencies are explicitly authored and complete in this fixture. Hidden dependencies from neural predicates are not represented. Multiple sufficient supports are represented structurally, not as cryptographic or causal proof.

## U
No GUI, OS input, model/provider, network, latency, token, production or authority claim. Derived facts remain evidence only; every row has `authority=none`.
