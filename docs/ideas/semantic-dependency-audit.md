# Semantic dependency audit before predicate-cache reuse

## Lineage: #4217, #4233, and #8883

### Prior scoped result: #4217 / PR #4225

The earlier predicate-cache result `PASS_DEPENDENCY_SCOPED_PREDICATE_CACHE_SCOPED` assumed the declared dependency set was complete. It established only the scoped behavior under that assumption; it did not test how an opaque evaluator's dependency set is found.

### Incomplete-declaration discriminator: #4233

#4233 changed the factor to dependency-declaration completeness and proposed fail-closed reuse when completeness is not established. Its allocation's terminal disposition remains `HOLD_AUDIT_CONTROL_HARNESS`: the first corruption wrapper crashed on a missing-row mutation, so the preregistered minimum corruption-control gate did not complete. Later read-only audit-v2 reconstructed 767 checks with no errors, and copied-evidence controls rejected 12/12 corruptions. Those later checks support auditability of retained evidence; they do not erase the first wrapper crash or relabel the consumed allocation as a PASS. Merged [PR #4249](https://github.com/Unjuno/agent-interface/pull/4249) preserves evidence only; #4233 remains open.

### Hidden-dependency discovery: #8883

**Status:** Open, unverified successor proposal; no runtime defect or result claimed.

#8883 asks whether a bounded black-box audit can find counterexamples to a declared predicate-dependency manifest before cached values are reused. The proposed principle is conservative: use controlled field interventions and an independent full-recompute oracle, but never treat absence of a counterexample in a finite set as proof of completeness. It is not a retry of #4233's 72-row allocation.

The intended next discriminator varies candidate fields independently and in selected interactions, compares cached versus full-recomputed outputs, and preserves UNKNOWN when the audit cannot establish coverage. Its exact preregistered factor set, budget, and decision criteria remain in [Issue #8883](https://github.com/Unjuno/agent-interface/issues/8883). No cache/runtime promotion, GUI operation, model call, or task input is authorized by the proposal.

## Evidence boundary

The results answer three different questions: whether caching is correct given a complete manifest (#4217), what happens when a known manifest is incomplete (#4233), and whether bounded interventions can discover omitted dependencies in an opaque evaluator (#8883). The first two do not establish the third. Finite intervention coverage can falsify a manifest but cannot prove universal semantic completeness without stronger assumptions.
