# Issue #3188 audit-v3 control-schema successor — preregistration

Allocation: `issue3188-audit-v3-control-schema-20260921-01`

This is a new bounded auditor-construction allocation. It does not repeat the formal-02 candidate execution or modify formal-02 evidence.

## H / T / D / C / U

- **H:** An independently written successor audit can bind each of the five named formal-02 controls to its exact Boolean condition vector, reject non-Boolean values, and continue to validate the unchanged raw and candidate source identities.
- **T:** Freeze this protocol on base `e6f74d3b9fef0467327823ab97cb15f0dbe59ac4`. Add code/tests only under `research/integration/issue_3188_source_bound_entry_gate_v1/audit_v3_control_hardening_v1/`. Target the exact formal-02 raw SHA-256 `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`, candidate `run.py` SHA-256 `e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822`, and candidate `audit.py` SHA-256 `72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d`. Freeze v3 source and test hashes in `FREEZE.json` before one test-suite invocation. Test baseline raw, the swapped `missing_receipt` guard, `false→0`, and a changed truth-table vector. The mutation copies remain in-memory only.
- **D:** `PASS_AUDIT_V3_CONTROLS_SCOPED` only if baseline structure and source/raw identity pass, and every preregistered mutation is rejected for the intended schema/value reason. A wrong acceptance or baseline mismatch is `FAIL_AUDIT_V3`; hash/setup/runner problems are `STOP` or `HOLD`. Preserve first outcomes; do not rerun the frozen suite under this allocation.
- **C:** Python-only offline audit construction. No model, game, GUI, X11, input, provider call, or mutation of formal raw. Docker Desktop is currently unavailable (service Stopped/Manual; no responding daemon), so the host suite is construction evidence only. Container validation is a separate outstanding gate and must not be relabeled PASS.
- **U:** Finite checks for this raw/auditor boundary only. This cannot replace the frozen formal-02 `HOLD_FROZEN_AUDITOR_DEFECT`, establish arbitrary auditor soundness, demonstrate workflow/CI equivalence, or support runtime/gameplay/product claims.

## Frozen control semantics

The expected control vectors come from the unchanged formal-02 raw and frozen runner semantics:

- `missing_receipt`: all five checks true except `terminal_integrity=false`.
- `stale_binding`: `matched_arm=false`; the other four checks true.
- `unknown_boundary`: `physical_task_effect_endpoint=false`; the other four checks true.
- `cleanup_failure`: all five checks true except `terminal_integrity=false`.
- `corrupt_recomputation`: `arm_bound_audit=false`; the other four checks true.

The intended oracle requires exact Boolean types (`type(value) is bool`), exact named row/value binding, exact row order/cardinality, and the existing fail-closed decision predicate. Python's `False == 0` equality must not satisfy a Boolean schema.

## Execution chronology

1. This preregistration is committed before v3 implementation.
2. Construction may include syntax/import checks, but not the frozen unit-test suite.
3. Freeze `independent_audit_v3.py`, `test_audit_v3.py`, and exact input identities in `FREEZE.json`.
4. Invoke the frozen unit-test suite exactly once; retain stdout, exit code, and raw hashes in `RESULT.json`.
5. Record the container gate separately. No retry, edit-after-freeze, or success promotion.
