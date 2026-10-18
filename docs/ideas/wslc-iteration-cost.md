# Same-host WSLc iteration cost — #6693

- **Source:** Open [Issue #6693](https://github.com/Unjuno/agent-interface/issues/6693), a migration-cost successor distinct from #6389's native Ubuntu/WSL2 versus WSLc portability pilot.
- **Status:** Unverified; the issue's latest readiness record (2026-10-08) reports candidate/auditor/paired blocks `0/0/0`. Do not infer a cost or memory result from #6337's single WSLc portability invocation or from later runtime availability.
- **Start boundary:** The proposed comparison requires explicit shared-lane ownership/release, an eligible same-host Docker arm, and exact source/image/dependency parity. Latest #6389 status (2026-10-08) retains `HOLD_SHARED_RUNTIME_OWNERSHIP_AND_CLEAN_CURRENT_MAIN_CHECKOUT_UNVERIFIED`; the latest #7970 comment (2026-10-12) records a start-gate deviation and stops further WSLc/Docker operations pending owner reconciliation. This page records those conditions; it does not authorize WSLc calls or a new run.

## Question and proposed comparison

For the fixed low-risk standard-library workload from #6315, can WSLc preserve byte-identical candidate output and the same independently audited 14/14 outcomes with 4/4 mutation controls rejected, while reducing same-host end-to-end iteration latency and/or peak host-visible memory versus Docker? The proposed comparison uses paired sequential Docker and WSLc candidate/auditor blocks on the same Windows host, randomized or counterbalanced order, and preregistered repetitions. It separates cold and warm startup, records total wall time and host-visible memory/PSI/swap, and requires at least a 10% improvement on one cost endpoint with no more than 5% regression on the other.

If runtime/image parity or safe ownership cannot be established, the proposal requires a pre-measurement HOLD. It explicitly prohibits induced memory pressure and says a configured WSLc cap is not evidence of enforcement. Any portability-only outcome would not support a speed or memory-benefit claim.

## Evidence boundary

- [#6315 / PR #6333](https://github.com/Unjuno/agent-interface/pull/6333) preserves the Docker/OrbStack finite candidate and corrected audit.
- [#6337 / PR #6352](https://github.com/Unjuno/agent-interface/pull/6352) established narrow WSLc portability on a different architecture/runtime condition: byte-identical raw output and a 14-case audit with 4/4 mutations rejected. Its single-launch timings are not a paired cost estimate and did not demonstrate an effective hard memory cap.
- [#6389](https://github.com/Unjuno/agent-interface/issues/6389) is the separate native Ubuntu/WSL2 versus WSLc pilot; [#7970](https://github.com/Unjuno/agent-interface/issues/7970#issuecomment-6118372633) records the 2026-10-12 gate deviation and request to stop further WSLc/Docker operations pending owner reconciliation. Neither is evidence that #6693's comparison ran.
- [#8518](https://github.com/Unjuno/agent-interface/issues/8518) is a related but distinct API-session reuse versus CLI-per-run break-even proposal.

No Docker-versus-WSLc speed, peak-memory, pressure, OOM-prevention, general compatibility, GUI, model, or product benefit is established. Preserve all predecessor outputs and do not convert the proposal's gate into a repository-wide pause.
