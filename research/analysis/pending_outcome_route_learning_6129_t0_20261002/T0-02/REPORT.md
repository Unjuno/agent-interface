# Issue #6129 T0-02 — typed endpoints and switching accounting

## H / T / D / C / U

- **H:** Pending-aware as-of summaries can preserve typed terminal states and intermediate YIELD, abstain on unknown censoring/state coupling, and account for explicit route-switch work.
- **T:** Seven finite cases at checkpoint 1/deadline 3: delay inversion pattern, null, declared independent administrative loss, safe-stop vs wrong-effect, YIELD/recovery, unknown outcome-dependent loss, and cross-task state coupling; plus fixed vs switching route paths.
- **D:** `PASS_METHOD_SCOPED`: independent auditor reconstructed 7/7 frozen checkpoint classifications/counts and exact switch accounting; tests 8/8 including no-lookahead and two corruption controls. Candidate and auditor exit 0, one invocation each, zero retries.
- **C:** Pinned OrbStack Docker, network disabled, read-only root/source, 0.5 CPU, 256 MiB, 32 PIDs, all capabilities dropped, no-new-privileges.
- **U:** This allocation is not the complete Issue T0. It does not independently calculate the exact delayed-complete-case ranking reversal from the eight-attempt construction, and its authored censor assumption is not empirically validated. No empirical route, task, product, safety or causal claim.

## Retained findings

At checkpoint 1, the YIELD attempt remains pending (not success, failure, or censor); safe stop and wrong effect remain separate; unknown censoring and state-coupled follow-up return UNKNOWN; the declared fixture permits a conservative selection only when bounds separate. The authored switch unit is 10 (reobserve 2 + handback 3 + release 1 + revalidate 4); path A-B-A costs 32 total units versus 12 for fixed A-A-A.

## Stop

Preserve this scoped run unchanged. Issue #6129 remains open: a new allocation must independently reconstruct the preregistered eight-attempt delayed inversion at checkpoint and deadline, explicit delay mechanism, policy comparison, no-lookahead, typed endpoint accounting, switch cost, and MODEL_MISMATCH boundary before the full T0 can be considered complete. T1/live routing remain unauthorized.
