# Service manifest / dynamic capability separation R0 — result

Decision: **PASS_SERVICE_MANIFEST_CAPABILITY_SEPARATION_SCOPED**

Issue #1607, parent idea #1597. Standard-library deterministic protocol-state analysis only.

## Analytical result

If a front-door service manifest is required to remain byte-stable during one service/protocol epoch while session capability state can change inside that epoch, directly embedding the mutable capability state cannot preserve both properties. For two times with different capability states, faithful direct encoding either changes manifest bytes or leaves at least one embedded state stale. A separately current capability snapshot/reference (or equivalent indirection) avoids that contradiction.

This is conditional on the #1597 design requirement of a small stable front door. A deliberately dynamic/non-cacheable service manifest is a different design.

## Formal result

One frozen invocation, seed `160720260918001`, 250,000 histories across four session scopes; reruns/replacements/tuning0.

- LINKED_SNAPSHOT candidate/oracle mismatch: **0**
- linked service-manifest hash changes: **0**
- linked invalid stale/future/wrong-scope snapshot authorizations: **0**
- linked supported selections: **150,000**
- linked fallback selections: **100,000**
- INLINE_CACHED stale support assumptions: **50,000**
- INLINE_REFRESHED manifest hash changes: **200,000 / 200,000 capability changes**
- revocations: **50,000**
- additions: **100,000**
- directed controls: **8/8**
- frozen source postformal rehash: **6/6**
- copied-result corruption controls: **5/5 rejected**
- independent audit: PASS, errors []

Hashes:
- RESULT.json: `55c76b51dc12413b9514c45cf41bbca24c882bb20dd67a199c23e73294903bb9`
- AUDIT.json: `dac68d0a6df2f9d25535fedba2e5cc57a63420f4d359a918064d74f313dff8fa`
- CORRUPTION.json: `0eb872cce0d77b5becf0cb3260f6ad898a05fc3a044978278619d1be1ecc5530`

## Design boundary

The scoped evidence supports one decomposition rule for a future #1597 manifest schema:

**stable service/protocol discovery belongs in the front-door manifest; mutable session capability set+generation belongs in a separately current object referenced by that manifest.**

The front door may declare how to find operation schemas, capability snapshots, event/control surfaces, authority/freshness semantics and the universal fallback, but it should not make cached manifest identity depend on mutable session capability contents.

No transport (HTTP/WebSocket/RPC/MCP), signature/security scheme, planner/token benefit, network reliability or production API is established here.
