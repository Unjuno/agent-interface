# Recovery review: #3217 retained postcondition reconciliation

## Disposition

Recover this additive evidence package into the current-main tree. The source branch is old and not an ancestor of current `main`, but its eight files are a retained independent audit result and exact raw/audit artifact that are not present on `main`. This is a byte-preserving recovery, not a new experiment and not a fresh Docker/Xvfb replication.

## H/T/D/C/U

- **H:** The retained workflow artifact is independently reconcilable against its frozen binding and row-level contract.
- **T:** Re-ran only the frozen raw-only auditor locally against the archived `artifact/raw.json`, `artifact/audit.json`, and `BINDING.json`; did not rerun a workflow or candidate experiment.
- **D:** `PASS_CURRENT_MAIN_ARTIFACT_RECONCILED_SCOPED`; 90 rows and 90 unique identities; no errors; all 6 corruption controls rejected. The reproduced result JSON is byte-identical to the retained `INDEPENDENT_AUDIT.json`.
- **C:** This preserves one synthetic verifier/auditor reconciliation. It does not validate GTK/X11 behavior, Docker replication, model utility, latency, or production performance.
- **U:** A fresh Docker/Xvfb experiment remains unperformed; do not infer it from this recovery.

## Byte and execution checks

The recovered `raw.json` and `audit.json` SHA-256 values match `BINDING.json`. The independent auditor, binding, freeze, and expected audit result match the frozen digests recorded in `FREEZE.json`. Local checks: Python compile, JSON parsing for all five JSON files, audit invocation exit 0, exact result comparison, and `git diff --check`.

## Integration boundary

All files are confined to `research/verification/postcondition_reconciliation_3217_v2/`. No historical evidence was edited, deleted, or relabeled. The original remote branch should only be removed after this PR is merged and every recovered blob is verified on `main`.
