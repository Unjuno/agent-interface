# Service Manifest discovery closure R1 — result

Decision: **PASS_SERVICE_MANIFEST_DISCOVERY_CLOSURE_R1_SCOPED**

Parent #1597; analytical parent #1607. Standard-library deterministic manifest semantics only.

## Reference contract tested

The stable front door exposes twelve required discovery queries:

1. service identity;
2. protocol identity + major version;
3. control relation;
4. observation relation;
5. operation-schema relation;
6. current capability-snapshot relation;
7. observation-representation catalog relation;
8. event/stream relation;
9. authority semantics;
10. freshness/currentness semantics;
11. handback/completion semantics;
12. universal fallback.

Mutable `session_capabilities` is explicitly forbidden in this stable manifest, following #1607.

## Formal result

One invocation, seed `162320260918001`, 180,000 manifests; reruns/replacements/tuning0.

- candidate/oracle mismatch: **0**
- silent invented discovery values: **0**
- canonical key-reorder mismatch: **0**
- valid accepted: **15,000/15,000**
- additive unknown-field accepted: **15,000/15,000**
- single required omissions accepted: **0/120,000**
- each of 12 required queries omitted exactly **10,000** times
- multi omissions accepted: **0/10,000**
- wrong-type accepted: **0/10,000**
- incompatible protocol major accepted: **0/5,000**
- forbidden inline session state accepted: **0/5,000**
- directed controls: **8/8**
- frozen source postformal rehash: **5/5**
- copied-result corruption controls: **6/6 rejected**
- independent audit: PASS/errors []

Hashes:
- RESULT.json `cf45d8e65169f4fa0b6479dcbcfbbf8c15017323e569267b897cf9fea6322aa4`
- AUDIT.json `aa662e26567506aaef016b9de92d47c6dbba9b3d5233e2d2f11c47a13e94bd57`
- CORRUPTION.json `d344247dd37e78885fb53a5e1320fa846cc4449005b3760c82b5c8a32f24795f`

## Interpretation

This validates one requirement-complete **reference** shape, not a globally minimal schema. The field/group names may change in a future ABI.

A stable API-agent front door can now be described without choosing a wire transport: stable identity/version; typed relations to control, observation, schemas, current capabilities, observation representations and events; explicit authority/freshness/handback semantics; universal fallback. Dynamic capability contents remain outside this object.

No HTTP/WebSocket/RPC/MCP selection, signing/security claim, planner usability, token saving, latency benefit or production compatibility follows.
