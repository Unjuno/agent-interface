# Trace-derived metamorphic relations

Issue #8904 proposes mining candidate metamorphic relations from retained finite traces, then independently validating and scoping them. The Issue is open and unverified; it does not claim universal validity, a runtime safety mechanism, or a current repository defect.

## Relation discovery for typed interface traces — #8904

- **Status:** open, unverified method-transfer proposal; no experiment, implementation, or evidence PR is recorded.
- **Source:** [Issue #8904](https://github.com/Unjuno/agent-interface/issues/8904); parent partial-oracle proposal [#5513](https://github.com/Unjuno/agent-interface/issues/5513).
- **Idea:** Mine candidate relations only from typed finite traces and declared transformation families; record support, exceptions, field dependencies, and observed scope. Freeze candidates before held-out validation against a separate semantic oracle. Finite absence of counterexamples yields at most `LIKELY_SCOPED`, never a universal relation or authority to act.
- **Proposed discriminator:** Compare manual #5513-style relations, independently validated inferred relations, and naive frequency-based mining at equal checking budget. Challenge them with opaque-ID renaming, declared-independent read-only permutation, meaningful-target changes, conflicting-action reorder, authority-epoch loss, effect-lineage changes, omitted preconditions, and held-out state/task shifts. An independent raw-only auditor should reconstruct candidate support, decisions, false alarms, mutant detection, and corruption controls.
- **Decision boundary:** `PASS_METHOD_SCOPED` requires at least one additional safety-relevant non-equivalent mutant detected beyond the manual baseline at equal budget, while valid held-out cases satisfy the declared relation and seeded false/shifted relations are rejected or marked UNKNOWN. Unsupported PASS on an authority/semantic violation is a failure; equal performance with no additional useful relation is `NO_INCREMENTAL_VALUE_SCOPED`. The proposal requires no live GUI, model, participant, network, or external allocation.

## Relation to other trace methods

#8904 discovers candidate partial oracles from trace transformations; it does not reduce a failing trace (#5666), generate smaller valid executions (#8878), or replace the typed relation and UNKNOWN contract in #5513. Any mined relation remains versioned, advisory, and bounded by its independently tested applicability scope.
