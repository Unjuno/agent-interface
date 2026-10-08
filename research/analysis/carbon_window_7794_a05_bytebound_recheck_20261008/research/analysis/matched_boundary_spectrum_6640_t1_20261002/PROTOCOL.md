# Frozen protocol — Issue #6640 T1

## H / T / D / C / U

**H.** In this finite synthetic cohort, within-stratum exposure contrasts should rank injected upstream fault boundaries earlier than pooled association and first-symptom order, while returning an explicit no-overlap state and making no causal claim from ranking alone. This may fail because a symptom or confounder can remain observationally indistinguishable.

**T0 screen.** Read-only inventory one retained cohort for exact attempt IDs, comparable task/route/model/scorer versions, exposures, and independent endpoints. The retained #6523 12-trace × 4-route fixture is authored event semantics, not a cohort of comparable independently labeled fault-boundary attempts. It lacks independent injected upstream/downstream fault identities needed for the spectrum. Disposition: `HOLD_NO_COMPARABLE_SPECTRUM` for empirical T0/T2. This hold does not cancel the independent, explicitly synthetic T1 method test and cannot be converted to an empirical claim.

**T1.** Deterministic CPU-only fixture: 32 fixed seeds × four task-difficulty/route strata × 64 attempts (8,192 rows). Each seed has one or two hidden injected boundaries (`admission`, `policy`). Candidate sees only task/route stratum, outcome, input-bound boundary exposures, missing exposure as JSON `null`, and first symptom. Independent oracle labels stay separate. `gateway` exposure is deliberately associated with difficulty but is not injected; `cache` has no within-stratum overlap; `render` is a post-failure symptom, not a pre-outcome exposure. The fixture also contains successful attempts despite active injected boundaries. Compare pooled risk-difference, equal-stratum matched risk-difference, first-symptom frequency, and deterministic random rankings. All rows and all 32 seeds remain in the denominator.

**D.** `METHOD_PASS_SCOPED` only if the matched rank improves predeclared first-true-boundary reciprocal rank over each baseline by ≥0.10 across all seeds, at least 75% of seeds retrieve every hidden boundary by top-2, every `cache` score is explicitly `NO_OVERLAP`, missing exposure remains distinct from unexposed, all attempt IDs are accounted for, and output states rankings are not causal evidence. Otherwise `FAIL_METHOD`; malformed/missing inputs or resource/provenance gate failures are STOP/HOLD, not a method result. Seed-specific synthetic ranks are descriptive, not population estimates.

**C.** Direct contract checks or raw failure counts may suffice. Stratification can remove a difficulty/route association but cannot by itself distinguish cause from a downstream symptom; the synthetic oracle is not an empirical causal label.

**U.** The fixture is authored, finite, and deliberately structured; it does not estimate natural failure prevalence, causal effects in a live interface, or inspection utility. Missingness, exposure definition, and strata choice can change rankings. No model, GPU, GUI, game, user, or consequential action is involved.

## Allocation

- ID: `MATCHED-BOUNDARY-SPECTRUM-6640-T1-CPU-20261002-01`
- Owner thread: `01a0b990-3d17-72f1-a908-9a2072104ce5`
- Base main at freeze: `3d768b0b1db255b5dacd099769a30a1b952a3f99`
- Branch/path: `research/matched-boundary-spectrum-6640-t1-cpu-20261002-r1` / `research/analysis/matched_boundary_spectrum_6640_t1_20261002/`
- Window: `2026-10-02T10:10:00Z`–`2026-10-02T10:30:00Z`
- Runtime: WSLc 3.0.1.0; pre-cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; pull never; network none; one CPU; requested memory 512M, but no effective enforcement claim due kernel/cgroup warning.
- Formal plan: one candidate invocation and, only if candidate exits zero and output exists, one separate raw-only auditor invocation. No retry, repair, tuning substitute, image acquisition, GPU, or network.
- Pre-existing WSLc containers: 36 exited, zero running and zero created at preflight. Do not remove or modify them. C: free space measured as 106,885,742,592 bytes at intake.

Construction checks are distinct from the formal candidate and audit. The formal output directories must be absent before execution.
