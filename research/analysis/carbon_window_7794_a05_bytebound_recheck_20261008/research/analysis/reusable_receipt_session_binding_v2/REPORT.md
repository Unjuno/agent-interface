# #1924 reusable receipt session/resource binding v2

Decision: **PASS_REUSABLE_RECEIPT_SESSION_RESOURCE_BINDING_SCOPED**.

## Result

The formal enumerated two caller sessions, two canonical focus resources, current=true/false, and every requested session/resource combination: **32 rows**.

- exact same-session + same-resource + current rows revalidated: **4**
- stale rows: **28**
- classification mismatches: **0**
- cross-session accepts: **0**
- cross-resource accepts: **0**
- stale-current accepts: **0**
- malformed/role/source control accepts: **0 / 5**
- persistent commit-bound receipts: **0**

## Repair relative to #1922

The retained #1900 bridge v1 admitted reusable evidence without caller applicability identity and was proven cross-session unsafe in #1922.

v2 keys persistent reusable receipts by the pair:

`(session_id, canonical_resource)`

and requires an exact key match plus current=true before reuse. This closes the concrete v1 laundering counterexample without weakening the #1858 role/scope/source/storage restrictions.

The v1 source and #1922 failure remain unchanged.

## Integrity

Frozen Git blobs matched before the one formal invocation:

- bridge: `f1ff26f51abfb4cbdeb77c6f23298f1f2fc7cb6c`
- formal: `8bf38e2f4161f10c8ab093ca6c81c5a8e79f96fb`
- audit: `1e5046e5d94ca4ca4fadf0520df54db44dec79bc`

Formal invocation1; reruns0; replacements0; tuning0.

## Limits

Session identity is intentionally narrow. A genuinely global reusable resource needs an explicit broader applicability domain and trustworthy canonical resource identity; wildcard cross-session reuse is not inferred. This is a bridge-local safety primitive, not executable adaptive-caller or GUI evidence.

## Next boundary

Any future executable #1900 successor must use v2 or stronger reusable binding semantics. The remaining empirical gap is still same-session caller composition with a real reusable receipt plus the already-retained fresh final gate.
