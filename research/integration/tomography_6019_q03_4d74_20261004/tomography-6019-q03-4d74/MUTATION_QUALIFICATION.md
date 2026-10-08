# Additive checker qualification

A new saved-data checker ran once in WSLc. Original accepted; eight frozen transformations rejected: persisted claim/disposition, endpoint clock, probe omission, global control, graph omission, hidden truth, aggregate metrics. First output and source freeze retained; no producer or predecessor auditor executed again. The copies exist transiently in memory and are exactly specified in mutation_qualification.py.

Source inspection shows the original heap auditor recomputes metrics from witnesses but does not compare persisted intervention_claim/disposition fields. Its first PASS_SAVED audit remains its narrow recorded result; do not call it a complete corruption-rejection gate. The new checker adds those semantic joins. It does not certify all possible mutations or source independence. This same-author supplement supplies ordinary archive validation, not formal method replication or nonauthor review.

Full Issue6019 T0 remains HOLD: swapped probe targeting, missing disjoint control, actual route switching, empirical clocks/no-start workloads and a strong covariance comparator are not all qualified by Q03. No runtime or statistical superiority promotion follows from eight rejected copies.
