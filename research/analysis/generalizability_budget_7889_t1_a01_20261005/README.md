# Issue #7889 T1 conditional read-only cohort audit

## Disposition

`HOLD_NO_IDENTIFIABLE_CROSSED_COHORT` at `origin/main` `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`.

The newest retained multi-arm #57 comparison is the A05 Chromium fixture in `research/integration/compiled_comparison_57_4d74_20261004/`. It has a task-crossed structure: arms A/B/C/D each have independent evaluation records for the same six task IDs in two counterbalanced blocks (48 assigned arm×task×block cells). Exact independent submissions total 45; three C-arm task noncompletions remain represented in the six-cell records. The retained accounting reconciliation covers 12 task assignments per arm; the A05 retained audit records all 48 tasks and all-attempt usage.

The evidence is one Chromium fixture and has no app/application ID in the independent per-block/per-arm outcome rows. Consequently, route-by-app variation cannot be estimated; this cohort cannot satisfy #7889 T1’s crossed task/app identity requirement or support a population route decision. The #12 artifact is a benchmark/oracle contract, not a second eligible route-comparison cohort.

## Method and evidence

`audit_t1.py` reads Git blobs from the pinned `origin/main` commit and writes only `t1-audit.json` in this output directory. It does not modify the retained source/result package and invokes no model, GUI, provider, or application. It checks the block/arm schedule, six task IDs and independent outcome counts per cell, 48-cell completeness, 45 exact/3 noncompletion accounting, duplicate/unexpected submission absence, all-attempt reconciliation, fixed-model identity, and app-ID availability. The checked source paths and SHA-256 hashes are retained in the JSON.

This was a new read-only structural check, not a replay of the old GUI run and not a complete semantic re-audit of every raw artifact. The existing A05 `RETAINED_EVIDENCE_AUDIT.json` explicitly scopes itself to post-run frozen identity/provider joins/independent scoring/native release, not a preregistered independent auditor. No missing app IDs or application cells were imputed.

The associated synthetic T0 remains `PASS_METHOD_SCOPED` at [the A01 report](../generalizability_budget_7889_t0_a01_20261005/REPORT.md). T0 does not overcome this T1 identifiability HOLD. A prospective T2 still requires separate source/owner/resource gates and a declared task/app population; no model or GUI allocation is authorized here.
