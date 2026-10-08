# Issue #6351 — cross-role meaning drift T0

**Disposition: `CONSOLIDATE_NO_INCREMENTAL_VALUE` (synthetic, method-scoped).** The flattened `COMPLETED` control lost two distinctions in eight fixed histories: a verified result with an unresolved child obligation and contradictory receipts. Direct typed-receipt answers and invariant-core role projections matched the frozen oracle on all eight. The audited projection therefore added no demonstrated correctness value over the existing typed-query baseline. This is not evidence about runtime receipts, external effects, models, or human interpretation.

## H/T/D/C/U

- **H:** Same evidence may be misread across planner, verifier, and effect/obligation owner roles when flattened; typed receipts/projections should preserve distinctions. Null: direct typed queries already suffice.
- **T:** One candidate run over eight deterministic non-handoff histories; compare flattened, typed and projected answers to independent oracle; audit every role field and apply mutations for epoch mismatch, dropped child, ACCEPTED-as-effect, and CONFLICT-as-PASS.
- **D:** Consolidate if typed and projection preserve every invariant and projection adds no correctness gain; fail if a projection loses an invariant; hold on invalid audit.
- **C:** Existing typed receipts may be sufficient; apparent drift may be caused by missing/stale events rather than presentation.
- **U:** Finite synthetic data only. No live runtime, model, human, effect, or product claim.

## Allocation history (all preserved)

1. **A01 `INVALID_AUDIT`:** Candidate/raw were generated once; the auditor hard-coded mutation detections and lookup counts (including an epoch check with no epoch field). Its inference is invalid. Exact output copies and original manifest are under [`invalidated-a01/`](invalidated-a01/); source files remain alongside them.
2. **A02 `STOP_SOURCE_MAIN_ADVANCED`:** Frozen main SHA advanced before formal allocation; candidate and auditor invocations were both zero. See [`../cross_role_meaning_drift_6351_t0_a02_v1/STOP.json`](../cross_role_meaning_drift_6351_t0_a02_v1/STOP.json).
3. **A03 candidate allocation:** One candidate invocation produced eight rows. Its first auditor omitted planner dispatch and effect-owner release/effect checks, so that audit was invalid for inference. Candidate/raw and invalid audit remain unchanged; see [`../cross_role_meaning_drift_6351_t0_a03_v1/`](../cross_role_meaning_drift_6351_t0_a03_v1/).
4. **A04 independent audit-only successor:** Candidate was not rerun. Separate auditor checked all 56 role fields across eight raw histories and rejected five field mutations. Result: `AUDIT_VALID`; all fields/oracle matched. See [`../cross_role_meaning_drift_6351_t0_a04_audit_v1/audit.json`](../cross_role_meaning_drift_6351_t0_a04_audit_v1/audit.json).

## Reproduction and evidence

Candidate and audit ran in OrbStack Docker using pinned local image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `python:3.12-slim`, network disabled, read-only root/input, 1 CPU, 256 MiB, 64 PIDs, all capabilities dropped, and no-new-privileges. Construction gates were separate. A04's one-shot command is `research/analysis/cross_role_meaning_drift_6351_t0_a04_audit_v1/RUN.sh`; its build failure/correction is retained in `BUILD_HISTORY.md`.

- 8/8 synthetic histories and 56/56 role fields matched the oracle.
- Flattened `COMPLETED` was emitted for 3 rows; 2 were false whole-task completions (unresolved child and conflicting receipts).
- Typed baseline: 8/8 correct. Projection: 8/8 correct. No demonstrated correctness advantage over typed baseline.
- A04 field corruption controls: 5/5 rejected.
- No issue closure or product change is warranted by this method-only result.

The independent audit validates only the frozen synthetic contract and the candidate bytes recorded in A03. It does not validate source event truth, effect occurrence, a production receipt schema, cross-agent behavior, human reliance, or general semantic interoperability.
