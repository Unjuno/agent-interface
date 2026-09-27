# Route capability dependency binding v1 — retained first outcome

Task `ROUTE-CAPABILITY-DEPENDENCY-BINDING-20260917-003`, Issue #842. BASE `f52f847c0fa5adf2af84c3689c8d58aa7f44f9f0`.

## Result

Decision: **`PASS_ROUTE_CAPABILITY_DEPENDENCY_BINDING_SCOPED`**.

The frozen formal runner was invoked exactly once over seven current-context cases. The route capability and `{scale,center}` semantics are held fixed; the only candidate addition is exact matching of the receipt's declared `session_id`, `surface_id`, and `geometry_epoch` against current context after the existing dimension check.

The exact-match case selects `ctrl_wheel` with `authority=none`. Session-only, surface-only, geometry-only, and all-three changes each return `STALE_CAPABILITY` with no selected route. A missing current geometry dependency returns `CURRENT_CONTEXT_INCOMPLETE`. A malformed retained-evidence identity returns `UNSUPPORTED_PROVENANCE`. The dimension-only baseline continues to select the route in every well-formed dependency-change case, exposing the stale-capability discriminator.

The frozen audit passes 7/7; a separately implemented verifier agrees. Six structured corruption controls (evidence identity, dependency escape, exact-positive over-invalidation, missing-context escape, authority escalation, and formal-count mutation) are all rejected.

## Integrity

- formal invocations: 1; reruns: 0;
- retained #803 center evidence Git blob: `28bc4a8c07958db58efe98eb73881cbced46c481`;
- source-first freeze commit: `3de2a4cdc98d7a730ae3f62fb5b2012718016602`;
- all frozen source SHA-256 values rehash exactly after formal;
- no GUI, model, device input, provider, network task or shared-runtime mutation occurred.

## Interpretation

This establishes one narrow admission property: **if** a capability receipt declares session/surface/geometry as dependencies, the admission layer can preserve its semantic dimensions while refusing that capability after those dependencies change. The result does not show that every route should be bound to all three dimensions, nor does it discover capability lifetimes automatically. Over-binding could cause needless invalidation.

The next useful step is not another synthetic receipt variant. It is a composed/live integration in which a real dependency changes and independent application scoring determines whether the declared capability lifetime is sufficient. Because live/formal control lanes may have separate ownership and leases, that successor should be coordinated against the active integration/real-time work rather than launched speculatively from this branch.
