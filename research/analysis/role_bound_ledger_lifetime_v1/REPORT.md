# #1848 role-bound mediated-ledger lifetime

Decision: **PASS_ROLE_BOUND_LEDGER_LIFETIME_SCOPED**.

## Result
Across 96 later-use states:

| policy | admissions | unsafe admissions | false rejections |
|---|---:|---:|---:|
| ROLE_BOUND | 1 | 0 | 0 |
| GENERIC_CACHE | 48 | 47 | 0 |

Storage behavior is also discriminating:

| evidence role | ROLE_BOUND | generic comparator |
|---|---|---|
| PREPARED_REUSABLE_VERSIONED | PERSIST_DEPENDENCY | PERSIST_GENERIC |
| FRESH_COMMIT_BOUND_CURRENT | EPHEMERAL_ONLY | PERSIST_GENERIC |
| unknown | REJECT | REJECT |

ROLE_BOUND persists one reusable dependency class and **zero** commit-bound receipt classes. Cross-intent/cross-commit replay admissions are zero; stale/FALSE/UNKNOWN/missing fresh-gate admissions are zero.

The generic comparator persists the earlier TRUE commit gate and exposes 47 unsafe later admissions.

## Interpretation
The two evidence roles established by #1835 require different storage semantics, not merely different labels.

A prepared reusable dependency is meaningful across time because its reuse condition is explicit semantic-version equality. A fresh commit-bound receipt is meaningful only at its bound intent/commit epoch. Its value cannot be converted into a reusable version merely because the payload is deterministic or because an earlier gate was TRUE.

Thus the #1792 mediated ledger needs two lifetime classes:
- durable/version-validated dependency state;
- ephemeral current commit evidence.

The latter may be transported, logged or audited after use, but must not participate in future admission as a cached positive currentness result.

## Relationship to earlier retained results
- #1471 and #745/#726 established broader evidence-role anti-laundering rules.
- #1792 established one mediated typed READ/RESOLVE/QUERY dependency ledger.
- #1823 established evidence-backed source admission for real source adapters.
- #1835 established that dependency validation and fresh commit gates are conjunctive and non-substitutable.
- This result closes the missing storage/replay rule for those roles.

## Integrity
Frozen source identities matched before the one formal invocation:
- formal `b359115d2e6d0d147672547d2b8e86c96d8036ef`
- auditor `8b6a7b3dd3b5d3d19bb3f512b813cd528e31816a`

Formal invocation1; reruns0; replacements0; tuning0.

## Limits
Deterministic ledger/cache semantics only. No GUI execution, model/token benefit, latency claim, production ABI or hostile-memory security proof.

## Roadmap disposition
The bounded autonomous roadmap selected after #1792 is complete:
1. #1823 — admit only evidence-complete real source adapters;
2. #1835 — separate prepared reusable dependencies from fresh commit-bound gates;
3. #1848 — enforce those roles at persistent storage/replay.

Remaining #1713 work is implementation/coverage against additional real observation, binding and capability sources. It should proceed under a new runtime-integration roadmap rather than extending this synthetic semantics ladder.
