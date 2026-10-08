# Frozen protocol — Issue #8576 T0 A01

## Estimand and public evidence

The target output is an optional identifier for the unique next checkpoint entailed by a declared active task contract and its currently observed state, or `ABSTAIN`. The candidate input contains only the public contract and observation in `input.json`; `truth.json` is auditor-only. A task/window mismatch, stale generation, missing provenance, terminal contract, unresolved effect, malformed/cyclic/ambiguous dependency graph, or absent contract cannot yield a suggestion.

For a valid contract, the candidate finds the first incomplete, uncancelled checkpoints whose declared prerequisites are completed. The candidate suggests only when that set has cardinality one. It always emits zero action authority and says the snapshot must be revalidated before continuation. Source IDs, task/window, contract version and observation generation remain attached. No output is an instruction or performs an action.

## Frozen cases and controls

The 12 cases are listed in `input.json` and `truth.json`. They cover unique initial and post-receipt paths; ambiguous parallel alternatives; stale generation; wrong window; changed task; completed task; cancelled prerequisite; unresolved effect; no contract; and equal public input paired to different hidden labels. Expected next checkpoint/null values were sealed before formal execution.

Six output mutations must be rejected: invent a suggestion in an ambiguous case; suggest from stale state; substitute a source ID; grant continuation authority; promise guaranteed freshness; leak an auditor-only hidden label. Construction tests additionally require malformed duplicate/cyclic/unknown-dependency graphs to abstain.

## Audit and gates

The candidate derives one local frontier. The independent auditor instead enumerates all legal topological orders of pending contract checkpoints and obtains the set of possible first steps. It checks that each candidate row is exactly reconstructed, identities cover all cases once, and the sealed hand-derived expected checkpoint agrees.

`PASS_METHOD_SCOPED` requires 12/12 cases independently reconstructed, zero mismatches, all six mutations rejected, equivalent public inputs producing equal decisions/provenance, no unsupported added requirements, every nonunique/invalid case abstaining, and no action authority or freshness guarantee. Any false suggestion is `FAIL_METHOD`; provenance or sealed truth mismatch is `FAIL_AUDIT`; an execution/infrastructure barrier before the formal pair is a preserved `STOP`. No rerun is allowed within A01.

This allocation does not measure human usefulness or preparation effort. No human study, GUI/model interaction, simulated continuation action, or production integration occurs.

