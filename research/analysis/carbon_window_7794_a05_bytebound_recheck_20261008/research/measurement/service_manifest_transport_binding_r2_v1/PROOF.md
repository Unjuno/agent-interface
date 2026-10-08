# Transport binding separation proof

Fix one service/protocol epoch and a byte-stable semantic manifest `M`. Let a logical relation `r` retain the same semantic meaning in this epoch while its concrete transport binding changes from `e1` at time `t1` to `e2 != e1` at `t2` (endpoint rotation or adapter switch).

If `M` directly and faithfully encodes the current concrete endpoint for `r`, deterministic decoding of the identical bytes `M(t1)=M(t2)` must return the same endpoint at both times. It therefore cannot equal both distinct current endpoints `e1` and `e2`; at least one decoded binding is stale.

If instead `M` is regenerated so that the embedded endpoint changes from `e1` to `e2`, then `M(t1) != M(t2)`, violating byte stability for the semantic front door.

Thus, under the stated stability requirement and unchanged semantic relation identity, mutable concrete transport binding must live in a separately current object (or equivalent indirection). This does not apply if concrete address is intentionally part of service identity and rebinding creates a new service epoch.
