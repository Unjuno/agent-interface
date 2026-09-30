# Allocation 02 — runner pass, independent audit STOP

Runner exit 0 and emitted `PASS_FEEDBACK_CONSTRAINT_SCOPED` for 20 synthetic rows. The independent raw-only auditor then exited 3 with `STOP_AUDIT_MISMATCH` on all four `pass_delivery_lost` policy rows. `AUDIT_STOP.json` preserves the exact error set and diagnosis.

The audit incorrectly defined `sequence_matches` as delivery-success AND sequence equality. The source model defines the field as equality between produced verifier sequence and required action sequence, independently of delivery; acknowledgement validity separately requires both delivery and equality. The missing-delivery row therefore has a matching sequence but no delivered acknowledgement. This is an auditor semantic defect, not evidence that the runner's safety result is independently reconciled.

Raw and runner summary are preserved unchanged. The auditor was not rerun and no post-hoc `PASS_AUDIT` is claimed. A separate allocation is needed to correct the independent oracle and rerun the frozen synthetic matrix.
