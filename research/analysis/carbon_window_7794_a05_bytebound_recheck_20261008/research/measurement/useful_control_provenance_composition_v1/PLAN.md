# Useful-control provenance composition v1 — construction

H: The independently constructed actuation-ID integrity (#953), effect-record exactly-once (#955), and temporal lower-bound (#950) gates compose in a fixed fail-closed order without changing parent #941 occupancy arithmetic or valid effect-role semantics.

T: Pure standard-library/container construction. Gate order: actuation lineage integrity/uniqueness -> effect-record ID integrity/uniqueness -> event-lineage identity -> nonnegative/pre-actuation temporal gate -> scoring/usefulness role. Fixed controls, 120,000 fresh mixed traces against an independent discrete oracle, and 30,000 malformed dataset controls. No #946 formal seed/corpus and no #869 live receipt.

D: Every mixed trace must match the oracle for all four occupancy bounds and every effect bucket; malformed sets must fail at the declared dataset-level gate; effect filtering must not alter occupancy.

C: Gate order defines precedence for multiply-malformed records; a future typed ABI may enforce some invariants before this layer.

U: Synthetic same-clock Python traces only. No X11/MAP01/planner-speed/production claim. Formal authorization is false.