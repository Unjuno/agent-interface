# V39 admission-derived key inventory join A01

Status: **PASS_ADMISSION_INVENTORY_JOIN_SCOPED**

On the retained V39 trace, 28/28 aggregate `keys_held` receipts exactly match their reconstructed per-step `input_admission` key sets. One canceled `Down` admission at `cover-4` step 10 remains unacknowledged/unmatched. Candidate and independent raw-only auditor agree.

Per-key admissions lack intrinsic `id`/`step`; the association is reconstructed from ordered event context, not a runtime-authored foreign key. No per-key key-up or live-control claim follows. See `PREREGISTRATION.md`, `FREEZE.json`, `candidate-output.json`, `audit-output.json`, and `SHA256SUMS.txt`.
