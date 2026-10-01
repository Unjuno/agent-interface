# #1792 mediated typed dependency ledger

Decision: **PASS_MEDIATED_TYPED_DEPENDENCY_LEDGER_SCOPED**.

## Result
One owner process held authoritative state and versions behind an AF_UNIX protocol. One separately exec'd task process received only a socket path plus a schedule containing `id` and `kind`; authoritative state was not in task configuration.

Formal coverage:
- branch READ cases: **16**
- alias RESOLVE+READ cases: **16**
- collection QUERY+READ cases: **32**
- malformed-operation negative: **1**

Across the 64 scientific cases:
- typed-ledger mismatches: **0**
- unsafe post-prepare validation acceptances: **0**
- false invalidations: **0**
- malformed-operation receipts: **0**

The malformed operation returns an error without fabricating dependency evidence.

## Composition
This integrates the primitive ladder that was separately retained under #165:
- #1756: control-predicate READ tracing;
- #1767: alias mapping + selected-object dependencies;
- #1773: query membership version + current-member reads;
- #1782: atomic writer maintenance of membership/query version.

The common mediator emits all three reader-side receipt kinds through one ledger. #523 separately established a stronger Linux filesystem/UID capability boundary against raw-store bypass; this experiment does not repeat that security result.

## Integrity
Before the one formal invocation, local source bytes matched frozen Git blobs:
- `run.py`: `4756835e787b156c6441c1cddfe58df635cf7e3e`
- `audit.py`: `13c56731fc02a35d5d4956ac2741652c73cc2f03`

Formal budget: invocation1, reruns0, replacements0, tuning0.

The retained deterministic formal bundle contains `RESULT.json`, `AUDIT.json`, `RAW_LEDGER.json`, `CASES.json`, and `TASK_SCHEDULE.json`; its decoded gzip SHA-256 is `e2c2b3d8cecd13b5f8881d54f6e79b4a39e58d76098b364104c40349c5d6ea43`. `restore_bundle.py` verifies the bundle and every individual file hash.

## Limits
This is a bounded protocol/mechanics integration, not arbitrary-code sandboxing, automatic GUI dependency discovery, production ABI promotion, latency/token improvement, or cross-platform evidence.

## Roadmap boundary
The autonomous roadmap selected in this run is complete at the typed dependency primitive/integration boundary:
1. derive a resource-footprint serializability contract;
2. transfer it to retained XTerm semantics;
3. complete READ/RESOLVE/QUERY/writer atomicity primitives;
4. integrate typed receipts through one mediated ledger.

Broader runtime adoption remains correctly open under #1713/#23 and should require a separate integration/runtime roadmap rather than silently modifying shared runtime from component evidence.
