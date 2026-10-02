# Issue #5537 T5 — approximate-section irreversible admission boundary

## H / T / D / C / U

**H.** A tolerance-based `APPROXIMATE_SECTION` result can be useful for reversible/compensable work, but must not authorize an irreversible effect unless the action contract separately and explicitly accepts approximation. Missing evidence (`UNKNOWN`) and inconsistent evidence (`NO_GLOBAL_SECTION`) must remain non-admitting. A solver that only emits a gluing status without carrying action class or policy can accidentally admit an approximate section.

**T.** Freeze a complete binary-valued three-variable context domain with two independently specified cases per context: an exact coherent equality cycle; a one-bit inconsistent parity cycle; one missing context; and an explicit tolerance-policy matrix. Enumerate all eight assignments for each complete bundle. Compare four admission policies: (1) exact-only for all actions; (2) approximate allowed for reversible/compensable only; (3) explicit action-contract override allowing approximate irreversible admission; (4) status-only unsafe baseline that admits any nonempty section set. Include tolerances 0 and 1, exact-spread, within-tolerance, and beyond-tolerance evidence, unknown coverage, and no-global-section controls. An independently written raw-only auditor recomputes sections, spread, status, action contract, and admission, and rejects frozen decision mutations.

**D.** `PASS_APPROXIMATE_IRREVERSIBLE_GATE_SCOPED` iff the exact coherent case admits both action classes; a within-tolerance approximate case admits reversible work but refuses irreversible work by default; the same approximate case admits irreversible work only under the explicit frozen action-contract override; beyond-tolerance, missing-cover, and empty-section cases never admit; tolerance=0 collapses to exact equality; and an independent raw-only audit verifies every row and rejects 5/5 mutations. Any default irreversible approximate admission is `FAIL_UNSAFE_APPROXIMATE_ADMISSION`; source/raw/schema mismatch is `STOP_AUDIT_MISMATCH`.

**C.** Finite synthetic relations and declared scalar spread/tolerance semantics only; this tests an admission-policy boundary, not real observations or safe numeric error budgets. The permissive `APPROXIMATE` action contract is an explicit modeling assumption.

**U.** No general sheaf solver, calibrated real-interface tolerance, freshness/provenance, authority authentication, GUI, model, task effect, empirical safety, or production correctness claim. T0–T4 artifacts/results remain byte-preserved. Host execution is used because no container lease is assigned; it is not Docker evidence.

## Freeze / execution protocol

- Intake/freeze base: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`.
- New isolated path only: `research/analysis/gluing_approx_irreversible_5537_t5_v1/`.
- Freeze candidate, independent auditor, fixtures, decision table, and exact Python/runtime before runner invocation. No GUI/model/network/external effects.
- One `python3 -B run_experiment.py` invocation. Only on exit 0, one separate `python3 -B audit_raw.py` invocation. No retry, tuning, or rewriting formal raw after the run.
- Record exact commands, exit codes, identities, raw/audit hashes, scope, and outcome. Preserve every STOP/FAIL as observed.
