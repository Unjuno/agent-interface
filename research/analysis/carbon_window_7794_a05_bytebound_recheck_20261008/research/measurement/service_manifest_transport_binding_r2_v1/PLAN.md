# Service Manifest transport binding R2

Task `SERVICE-MANIFEST-TRANSPORT-BINDING-R2-20260918-001` / Issue #1644.

## H
With a byte-stable semantic service manifest and transport bindings that may change inside the same service/protocol epoch, embedding concrete endpoint bindings directly in the manifest cannot preserve both stable semantic identity and binding freshness. Stable logical relation IDs plus a separately current transport binding can preserve both.

## T
Standard-library deterministic protocol-state model. Compare `INLINE_ENDPOINT`, `INLINE_REFRESHED_ENDPOINT`, and `LOGICAL_RELATION_BINDING`; independent oracle; directed controls; then one 240,000-history formal corpus across four sessions and two abstract adapters. Exactly 60,000 stable histories, 60,000 endpoint rotations, 60,000 adapter switches, and 60,000 relation-withdrawal/fallback histories. Every history also probes stale/future/wrong-service/wrong-protocol binding variants. No real network or runtime.

## D
PASS iff candidate/oracle mismatch0, stable semantic-manifest hash changes0, invalid binding authorizations0, current bound selections>0, fallback selections>0, cached-inline stale endpoint selections>0, refreshed-inline manifest hash changes equal all binding changes, endpoint rotations>=50,000, adapter switches>=50,000, directed controls/source/audit/corruption pass, formal1/reruns0.

## C
A deployment may define concrete address as service identity, making address change a new service epoch. This R2 applies to the parent goal of one semantic interface across adapters/transports.

## U
No wire protocol, network reliability, authentication/signing, planner usability, latency or token claim.
