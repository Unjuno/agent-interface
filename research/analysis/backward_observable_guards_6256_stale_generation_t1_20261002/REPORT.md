# #6277 audit-only T1 result — stale-generation mutation

**Successor disposition: `PASS_REQUIRED_MUTATION_COVERAGE_SCOPED`.** One independent raw-only audit completed with zero errors. Candidate/runtime invocations: 0; retries: 0. The original #6256 T0 files and their disposition are unchanged.

## Reconciliation

The byte-pinned T0 model, candidate output, and original audit output match their frozen SHA-256 identities. The independent checker recomputed all 13 outcome predicates and the universal preimage over 10 states; it matches the T0 candidate's three preimage states: `ready_complex`, `ready_simple`, and `unobservable_safe_alias`. The 5 prior mutation counterexamples were independently reconstructed from the immutable model; all 5 matched the original audit receipt.

The added mutation removes only `generation_fresh` from the exact guard. The exact guard returns REFUSE for `stale_generation`; the mutated guard returns ADMIT. Its sole outcome is `wrong_target_saved` and includes the forbidden prefix tag `wrong_target`; it is not in the exact preimage. This is the missing stale-generation mutation control requested by #6256.

The six scoped mutation counterexamples are: existential success over an unreliable save; dropping forbidden-prefix checks; pixel-only equivalence; dropping verified release; dropping bounded termination; and dropping generation freshness. This audit closes only the omitted mutation coverage, not the entire #6256 T0 review gate.

## Relationship to parent T0

PR #6276's T0 raw candidate and audit remain byte-unchanged. Its `PASS_METHOD_SCOPED` and overall `HOLD_INCOMPLETE_MUTATION_COVERAGE` remain the exact historical T0 outcomes. This T1 is a separate audit-only allocation, not a retroactive rerun or reclassification. The full #6256 study still needs review of the T0 plan's remaining comparison requirements (including the forward-only proposal-checker comparator and observation-cost treatment); this scoped pass does not imply those were measured.

## Scope

Pure local CPU audit of an authored finite synthetic model. No container was required or touched. It does not verify transition-model completeness or real GUI semantics and makes no claim about live safety, effect, authority, task success, latency, efficiency, or product utility.

Inputs, frozen auditor, construction tests, raw audit output, run record, and hashes are retained in this package.
