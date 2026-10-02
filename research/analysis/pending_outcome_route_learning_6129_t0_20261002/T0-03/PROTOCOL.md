# Issue #6129 T0-03 — delayed inversion and typed outcome audit

## H/T/D/C/U

- **H:** Complete-case selection can rank B above A at checkpoint 1 while the frozen deadline-3 all-attempt endpoint ranks A above B. Conservative pending bounds must withhold that premature choice; typed terminal outcomes, censoring, recovery, and route-switch work remain distinct.
- **T:** Seven exact finite cases. The eight-attempt delay table is explicit by attempt, terminal label, and terminal time; includes equal-delay null, known-independent administrative loss, safe-stop vs wrong-effect, YIELD then later terminal recovery, unknown/outcome-dependent loss, and cross-task state coupling. Candidate receives only `visible.json`; auditor receives `truth.json` separately.
- **D:** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs checkpoint counts, complete-case selection, pending-aware decision, deadline inversion rates, typed terminal distinctions, no-lookahead consistency, exact switch charge, and all seven expected case dispositions; mutation controls must be rejected.
- **C:** Authored finite CPU-only fixture, exact rational arithmetic, no model/live calls, no user data. One candidate and one auditor invocation in distinct pinned, network-disabled OrbStack Docker containers; read-only input/source mounts, separate output mount, fixed limits.
- **U:** Method demonstration only. The known-independent loss label is a fixture assumption; not empirical identification. No route efficacy, actual task, causal/product/safety, live routing or delayed-bandit theorem claim. Cross-task case only gates out a misspecified independent-arm interpretation.

## Frozen endpoint and cost semantics

Primary endpoint is verified success by deadline among all assigned attempts. `VERIFIED_FAILURE`, `VERIFIED_WRONG_EFFECT`, `POLICY_TERMINAL_SAFE_STOP`, true administrative loss, unresolved pending, and intermediate `YIELD` remain separate. At checkpoint 1, A's only resolved attempt is a failure and B is 2/4 successes: complete-case rates are A=0 and B=1/2. Pending-aware bounds are A=[0,3/4], B=[1/2,1/2], so the intervals overlap. By deadline 3, all-assigned success rates are A=3/4 and B=1/2. The candidate cannot access that future table.

Switching cost: reobserve 2 + handback 3 + release 1 + revalidate 4 = 10 work units per route change. The authored `A,A,A` path costs 12 base work; `A,B,A` costs 12 + 2*10 = 32. This is a sensitivity/accounting control, not a measured system cost.
