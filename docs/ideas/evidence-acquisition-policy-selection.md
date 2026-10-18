# Assumption-gated evidence acquisition — #8879

- **Status:** Unverified algorithm-selection and evaluation-method proposal.
- **Source:** [Issue #8879](https://github.com/Unjuno/agent-interface/issues/8879), successor to the method gap exposed by [#5306](https://github.com/Unjuno/agent-interface/issues/5306) and [#6190](https://github.com/Unjuno/agent-interface/pull/6190).
- **Idea:** Test whether a finite evidence-acquisition problem can cheaply determine when adaptive diminishing-returns assumptions justify greedy selection, and when a bounded lookahead policy is preferable. Include certificate and planning overhead in the choice.
- **Outcome:** No implementation or result is recorded. The proposal does not claim that GUI observations satisfy adaptive-submodularity assumptions, provide an approximation guarantee for runtime use, or demonstrate an Agent Interface benefit. It does not amend or rerun #6190's retained counterexample.

## Smallest useful test

Use a finite exact-rational decision tree with a small set of observations, costs, deadlines, and explicit outcome dependencies. Include cases where adaptive diminishing returns holds, plus complementary, redundant, correlated/common-cause, stale, and infeasible observations where it fails. Compare greedy, fixed depth-2/3 lookahead, exact Bellman, and a certificate-gated portfolio; separate calibration cases from held-out cases. Keep mandatory safety checks outside policy selection and count the certificate's compute cost.

An independent auditor should reconstruct reachable histories, conditional marginals, policy paths, expected loss, and overhead. Reject a false certificate, any skipped mandatory check, or any upgrade of UNKNOWN. If no bounded policy has a robust benefit after overhead, retain STOP/YIELD and record no selection value. A finite pass would establish only method behavior on the frozen model family, not live GUI latency, model value, or runtime safety.
