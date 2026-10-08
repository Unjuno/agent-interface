# STOP — acceptance gate failed after raw audit

Allocation: `quiescent-epoch-binding-5361-t1-20260930-01`

The formal runner and raw-only audit each executed once. The audit returned `PASS_READONLY` with no structural/oracle errors. However, an adversarial post-audit review of the frozen gate found that `EPOCH_BOUND` reclamation checks the reader set, retired authority label, and registry generation but does **not** bind the quiescence receipt to the retired epoch. A receipt from a different epoch with matching reader IDs, authority label, and registry generation would satisfy the implemented reclamation predicate.

Therefore the preregistered D condition requiring epoch-bound receipts is unmet: disposition is `FAIL_GATE_INCOMPLETE`, not PASS. The raw and audit are preserved unchanged. No repair, retune, or rerun was made. A new successor allocation must add an explicit receipt-epoch mismatch negative control and a separate independent audit check.

This reveals a gap in the assurance gate, not a production incident or evidence that an external object was reclaimed. The experiment is a deterministic synthetic model only.
