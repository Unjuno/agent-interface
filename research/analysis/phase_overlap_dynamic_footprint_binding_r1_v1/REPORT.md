# Dynamic footprint binding — analytical R1

Issue #1742. Successor to #1730.

Disposition: `PASS_DYNAMIC_FOOTPRINT_BINDING_SERIALIZABILITY_SCOPED`.

## Result

Exhaustive finite analysis over 8 initial states and 12 deterministic B operations (1,152 B input/tail cases):

- STATIC_SUPERSET admitted 8 cases; mismatches 0.
- RESOLVED_BOUND admitted 200 cases; mismatches 0.
- RESOLVED_BOUND adds 192 cases beyond STATIC_SUPERSET; all 192 are serial-equivalent.
- RESOLVED_BOUND admitted selector-writing B phases 0 times.
- RESOLVED_UNBOUND_NEGATIVE admitted 512 and produced 128 mismatches.
- UNKNOWN admitted overlap 0 times.

The minimal negative witness starts S=0,X=0,Y=0. A prepares target X. B writes S=1 before A tail. If the resolved footprint omits selector S, overlap is admitted and A re-reads S=1, toggling Y instead of serial execution's X. Final overlap state S=1,X=0,Y=1 differs from serial S=1,X=1,Y=0.

Independent audit PASS; corruption controls5/5 rejected.

## Interpretation

A runtime-resolved narrow footprint can safely recover concurrency relative to a static superset in this deterministic model, but the state that selected the footprint must remain a first-class read/currentness dependency. The resolved target alone is insufficient authority.

This is conditional on complete selector/resource modeling. Aliasing, hidden globals, external mutation, multi-resource data-dependent access and revalidation cost are outside scope.
