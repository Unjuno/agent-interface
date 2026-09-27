# #1835 two-tier reusable dependency + fresh commit gate

Decision: **PASS_TWO_TIER_DEPENDENCY_COMMIT_GATE_SCOPED**.

## Result
Across the full 24-state Cartesian product:

| policy | admissions | unsafe admissions | false rejections |
|---|---:|---:|---:|
| TWO_TIER | 2 | 0 | 0 |
| DEP_ONLY | 12 | 10 | 0 |
| GATE_ONLY | 4 | 2 | 0 |
| CACHED_GATE | 6 | 5 | 1 |
| SCALAR_ALL_CURRENT | 1 | 0 | 1 |

The exact safe oracle is:

`prepared dependencies current AND fresh gate lineage current AND fresh gate TRUE/LIVE`.

## Why both layers are necessary
A reusable dependency receipt describes state that influenced preparation and may be validated by version equality later. It cannot substitute for a fresh target/effect gate whose truth may change after preparation.

Conversely, a fresh target/effect gate cannot prove that the reasoning which selected the action still rests on current dependencies.

The retained unsafe witnesses expose both directions:
- DEP_ONLY admits with current prepared dependencies even though the fresh gate is FALSE/stale.
- GATE_ONLY admits a fresh TRUE gate while the prepared dependency set is stale.
- CACHED_GATE admits a prepare-time TRUE after the current gate has become FALSE/stale.

## Role/lifetime contract
The formal retains two distinct evidence roles:
- `PREPARED_REUSABLE_VERSIONED`
- `FRESH_COMMIT_BOUND_CURRENT`

They may share transport or be fused into one opaque implementation token only if both semantics and lifetimes remain independently enforceable.

Treating all evidence as a single scalar currentness condition can remain safe but is unnecessarily conservative: the frozen scalar control rejects one of the two oracle-valid rows.

## Relationship to retained evidence
- #1792 establishes a reusable mediated READ/RESOLVE/QUERY ledger.
- #1823 establishes that real sources require evidence-backed source completeness before becoming reusable dependencies.
- #878 and #1650/#1652 establish fresh current target/VERIFY gates that fail closed on missing/stale/unknown evidence.

This result supplies the missing composition boundary: reusable dependency validation and fresh commit-bound evidence are conjunctive, not interchangeable.

## Integrity
Frozen source identities matched before the one formal invocation:
- formal `1482c4fda45d6bed7b4ccfd9b1e0e0307b1d2805`
- auditor `408937a825bacadb10e7f406309ced6776bf1cbf`

Formal invocation1; reruns0; replacements0; tuning0.

## Limits
Finite synthetic semantics only. No GUI execution, model/token benefit, latency gain, production ABI, or cross-platform claim.

## Next rung
Apply the role distinction to the mediated ledger itself: reject attempts to store or replay `FRESH_COMMIT_BOUND_CURRENT` receipts as reusable dependency versions, while allowing `PREPARED_REUSABLE_VERSIONED` receipts to persist until their versions invalidate.
