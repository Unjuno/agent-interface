# Issue #6284 — cross-handoff pending-correction T0

**Combined decision: `H_FAIL_SCOPED / SUBSUMED_BY_24_5817` for incremental value beyond the stronger comparator on the seven frozen synthetic histories.** The baseline phenomenon is constructible under visible-state-only and typed-handoff policies, but the proposed correction-conservation arm does not outperform #24 retry identity plus #5817 complete effect/resource-footprint obligation accounting in these cases.

## Results

- Formal-01: six histories, four policy arms; candidate and independent event-table oracle agree exactly. Each ran once in a separate OrbStack Docker container and exited 0. Network disabled; read-only root and source; non-root UID; all capabilities dropped; no-new-privileges; 0.5 CPU, 256 MiB, 64 PIDs.
- Four same-goal overlapping histories (delayed accepted effect/new intent, three-owner partial/late effect, dedupe expiry/new intent, canonical resource alias) admitted duplicate proposals under visible-state-only and typed handoff. The #24+#5817 D arm held the overlapping new intent in each case. C made the same admission decisions as D; no incremental C-over-D effect was observed.
- Unknown footprint produced `HOLD_UNKNOWN_FOOTPRINT`; it was not treated as disjointness. Mandatory safety release bypassed the normal correction gate.
- Formal-01 omitted an actual post-goal-change independent-work proposal, so its preregistered gate was incomplete. The first Docker client command also failed before container creation because of a cidfile path typo; no code ran in that attempt. Both are retained in formal-01 `RUN.json`; the single formal candidate and auditor then completed without retries.
- A separately frozen successor allocation added the missing changed-goal positive control. Formal-02 candidate and independent audit both exited 0: while old `op-A` remained unresolved under goal-1, D admitted disjoint `op-B` for goal-2 and did not falsely discharge `op-A`.
- Local construction/adjacent suites: 6/6 for this package, 8/8 for `endogenous_demand_rebound_5702_t0_v1`, and 12/12 for `selection_aware_shadow_audit_5681_t1_v1`. Repository analysis index: 371 result/failure directories indexed. Public navigation: 26 documents / 1207 links; all passed locally against refreshed main `0b8fcbd1e` plus this package.

## Interpretation and boundary

This is a finite synthetic-method falsification, not evidence that real agents exhibit cross-handoff amplification. On these authored histories, per-intent retry identity alone does not stop a distinct new intent, while a complete shared effect/resource identity in the #5817 obligation ledger does. Correction conservation provided no extra block beyond that comparator and preserved the tested independent changed-goal task and safety release. This does not establish production footprint completeness, durable ledger implementation, or improved real task safety, latency or success. No implementation or T1 follows from these results.

## H / T / D / C / U

- **H:** Not supported as an incremental mechanism over D on this fixture family; weaker visible-state-only and typed-handoff comparators did admit duplicate proposals.
- **T:** Seven discrete histories across two frozen allocations; four policies; independent reconstruction; two isolated candidate/auditor container pairs; no model, network, GUI, human or shared data.
- **D:** `H_FAIL_SCOPED / SUBSUMED_BY_24_5817` for incremental value: D blocked every planted same-goal overlap, failed closed on unknown footprint, admitted tested disjoint changed-goal work, and retained mandatory release. C did not outperform D.
- **C:** This matches #6284's updated overlap audit: complete effect identity/footprint in #24/#5817 may subsume the proposed mechanism.
- **U:** Finite synthetic semantics only; no real-world prevalence, application-footprint completeness, durability, GUI effect or human-outcome evidence.
