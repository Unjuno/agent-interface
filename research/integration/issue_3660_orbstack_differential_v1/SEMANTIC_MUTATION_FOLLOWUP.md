# Issue #3660 semantic mutation follow-up

This additive follow-up extends the already merged OrbStack audit's synthetic mutation suite with two resealed semantic corruptions:

- `focus_active_wrong_resealed`: change the focus-drift active XID to Calc's window, then recompute every event hash and sequence.
- `modal_parent_wrong_resealed`: change the modal parent to Inkscape's window, then recompute every event hash and sequence.

Both must return `FAIL_AUDIT_INTEGRITY`. These controls complement the merged nine-mutant suite; they do not change the immutable #3652 raw or its audit disposition. The untouched input remains `HOLD_AUDIT_EVIDENCE_INCOMPLETE`.

## Observed bounded result

- WSL Ubuntu, native (not a container): `PASS_MUTATION_CONTROLS`, zero failures across untouched + runner-boolean control + 10 adversarial changes.
- Untouched raw SHA-256 remained `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883`; decision remained `HOLD_AUDIT_EVIDENCE_INCOMPLETE`.
- `focus_active_wrong_resealed` SHA-256: `366e88e74d0bea6dc84eef51627c48ad63193d7813ae80c153065dd2cbdcb4a2` → `FAIL_AUDIT_INTEGRITY`.
- `modal_parent_wrong_resealed` SHA-256: `661de8bdbb6799e77cdd1285d3ace4878bc1f1885becacdb8da53fcd329f8ecf` → `FAIL_AUDIT_INTEGRITY`.
- The frozen predecessor readback auditor rejected both of these semantic controls, while it accepted the five already documented resealed protocol/count mutations (reorder, extra event, input counts 2/4/true). No historical result was edited.

## H/T/D/C/U

- **H:** The merged auditor rejects semantically inconsistent focus and modal receipts even when per-event hashes and sequence numbers are correctly recomputed.
- **T:** Run the existing `test_audit_raw.py` against the immutable `evidence/frozen_3652_formal01_raw.json`, directing generated mutant files to a fresh temporary output directory. The existing predecessor auditor is replayed against the same mutations. No GUI, model, network, or input.
- **D:** PASS only if both new cases are `FAIL_AUDIT_INTEGRITY` under the new auditor, the untouched case remains HOLD, and no mutant is accepted by the independent gate. Preserve all earlier mutation/result artifacts unchanged.
- **C:** Same frozen raw SHA-256 `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883` and merged auditor; only two synthetic corrupted copies are new.
- **U:** This adds assurance only for these two event-field mutations; it does not create missing observations, retroactively upgrade the historical transitions, or establish runtime behavior. Docker Desktop is unavailable locally, so the bounded test runs in WSL Ubuntu, not a container.
