# Preformal stop — causal lineage identity type gap

The #946 formal corpus was **not executed**. Formal invocation/rows/reruns remain `0/0/0`.

After claim and before formal, an independent read-only review identified that the exact merged candidate relies on Python annotations rather than runtime validation for `Actuation.actuation_id`. Reproduction against exact Git blob `979f257...` confirms that `None`, `''`, and integer `0` are accepted as actuation IDs. If an independently scored useful `EffectEvent` carries the same value, `classify_effects()` reports `useful_bound=1`.

This is not an interval-arithmetic mismatch. It is a causal-lineage/provenance admission gap. `None` is particularly ambiguous because `EffectEvent.actuation_id=None` is also the representation for unbound lineage.

The frozen #946 decision intent included fail-closed malformed/ambiguous identity. Therefore the 20,000-case arithmetic formal was not consumed merely to obtain a scoped arithmetic PASS in the presence of a known provenance contradiction.

A successor must use a fresh task identity and may change exactly one mechanism: runtime validation of causal actuation identity (for example, a non-empty string requirement), while retaining the exact interval arithmetic and evidence-role semantics. No #869/X11/live allocation was touched.
