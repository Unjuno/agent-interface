# GUI target late binding v2 — cross-domain transfer

## Decision

**PASS_CROSS_DOMAIN_LATE_BIND** with `PASS_AUDIT`.

The experiment transfers the execution-time evidence-binding rule retained on MAP01 into a real Inkscape/X11 target-edit task. A durable high-level subgoal is fixed: delete `task-target` and save. During the same 6.5 s deterministic decision wait, the harness pans the canvas three times in both arms. The sole scientific difference is whether target evidence remains bound to the pre-wait screenshot or is freshly reacquired after the wait.

## First complete v2 result

V1 retained five completed first outcomes and then stopped before the remaining cases after an outer multi-case harness timeout. It has no scientific disposition and is not pooled. V2 changes orchestration only: one private desktop per outer launch, new formal seeds, identical science.

V2, four fresh seeds / eight cases:

- `snapshot_bound`: stale **4/4**, safe zero-task-input yield **4/4**, exact SVG unchanged **4/4**, release failures **0**; median evidence age **6.503 s**.
- `late_bind`: fresh **4/4**, bounded unique visual reacquisition **4/4**, persisted target-only delete/save **4/4**, wrong-object edits **0**, release failures **0**; median evidence age **20.206 ms**.
- paired median `(snapshot age - late-bind age)`: **6.483 s**.

The frozen PASS gate required all snapshot arms to fail closed with exact unchanged SVG, all late-bind arms to reacquire uniquely and produce only the requested persisted effect, zero release/wrong-target failures, and >=5 s paired age separation. All gates passed.

## Independent audit

The audit does not trust the resolver receipt or task outcome flag. For every late-bind case it independently re-derives the source target from the retained pre-wait RGB pixels, rebuilds the outline-containing template, reruns the frozen bounded resolver on the post-wait PNG, and parses the persisted SVG before/after to require removal of only `task-target` with the canvas and every other object unchanged. Snapshot cases require stale evidence, zero task input and exact SVG byte identity. All InputOwner release records are rechecked.

## Interpretation

The narrow mechanism transfers across domains: a planner-level intent may survive a long decision delay while the environment-dependent target binding does not. A stale source observation can safely expire with no task input; the runtime can later derive a fresh, no-authority target reference and only then admit the operation.

This is not proof of semantic identity under pixel-identical object replacement; that observability boundary remains separate. The target/reference fixture is authored, the wait is deterministic sleep rather than a frontier-model call, and this is one fixed-scale Inkscape fixture family. No general GUI speedup, broad reliability, model efficacy, or MAP01-clear claim follows.
