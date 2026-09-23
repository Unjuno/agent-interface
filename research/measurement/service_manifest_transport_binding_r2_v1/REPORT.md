# Service Manifest transport binding R2 — result

Decision: **PASS_SERVICE_MANIFEST_TRANSPORT_BINDING_R2_SCOPED**

Parents #1597 / #1598; analytical parents #1607 and #1623.

## Analytical result

Within one service/protocol epoch whose semantic front-door manifest is required to remain byte-stable, a logical relation whose concrete endpoint can rotate or move between transport adapters cannot directly and faithfully encode that current endpoint in the same stable manifest at all times. If bytes stay fixed, one endpoint becomes stale; if bytes refresh with the endpoint, stable manifest identity is lost.

Therefore the scoped parent design is cleaner as:

```text
stable semantic manifest
  relation: rel.control
       |
       v
current transport binding
  (service_id, protocol_major, transport_epoch, adapter)
  rel.control -> opaque endpoint
```

Concrete endpoint syntax remains transport-specific and outside the stable semantic object.

## Formal result

One deterministic invocation; seed `164420260918001`; **240,000** histories; reruns/replacements/tuning0.

- stable histories: **60,000**
- endpoint rotations: **60,000**
- adapter switches: **60,000**
- relation withdrawals/fallback: **60,000**
- candidate/oracle mismatch: **0**
- stable semantic-manifest hash changes: **0**
- stale/future/wrong-service/wrong-protocol binding authorizations: **0**
- current bound selections: **180,000**
- universal fallback selections: **60,000**
- cached-inline stale endpoint selections: **180,000**
- refreshed-inline manifest hash changes: **180,000 / 180,000 binding changes**
- directed controls: **11/11**
- postformal source rehash: **8/8**
- copied-result corruption controls: **6/6 rejected**
- independent audit: PASS, errors []

Hashes:
- RESULT.json `28e014a2502a29dd3b68c986b00c0832bd2655ff6630ff7f794c029ecd44355b`
- AUDIT.json `e80318a9dfa055b59dad53f40144127db40a8b75b58910f0ac1bfa6d1b196db8`
- CORRUPTION.json `616d4a179908fadc8fb4fbca11cc6024f3aef2cae4c8b17af5914fcff5c254e1`
- SOURCE_REHASH.txt `d1cb50cbe257f6c6bbb10eb2b9971c6ea0183df5846222f299bddcc3dbf74e71`

## Preformal integrity chronology

Initial remote readback was 7/9 exact because four comment-only lines in local `construction.py` / `formal.py` were absent from the published source strings. Formal remained0 and the seed unused. The remote executable source was adopted as canonical, the source manifest alone was refrozen, excluded construction remained11/11 PASS, and subsequent remote readback was9/9 exact before formal.

## Boundary

This proves a transport-binding decomposition for the parent requirement; it does **not** select HTTP, WebSocket, RPC, MCP or any URI syntax. It also does not establish authentication/signing, network reliability, planner usability, token saving or latency benefit. A deployment that intentionally makes the concrete address part of service identity can instead start a new service epoch on rebinding.
