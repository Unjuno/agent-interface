# Service manifest / dynamic capability separation R0

Task SERVICE-MANIFEST-DYNAMIC-CAPABILITY-SEPARATION-R0-20260918-001 / Issue #1607.

H: a byte-stable service front door and mutable session capabilities cannot be the same directly encoded object across capability changes without sacrificing either stability or freshness. Linked, generation-bound capability snapshots can preserve both.

T: analytical proof, directed controls, then 250,000 seeded histories over four sessions. Compare INLINE_CACHED, INLINE_REFRESHED, LINKED_SNAPSHOT against an independently structured oracle. No network/runtime/model/GUI.

D: PASS iff linked mismatch0, service-manifest hash changes0, stale support0, supported choices>0, fallback always discoverable; cached inline has stale support>0 under revocations; refreshed inline changes manifest hash on capability changes; stale/future/wrong-scope snapshots never authorize; malformed manifest controls reject; formal1/reruns0.

C: if the service manifest is intentionally dynamic/non-cacheable, stable-front-door separation is not required. Transport representation remains unspecified.

U: protocol-state semantics only; no user/token/network/security benefit claim.
