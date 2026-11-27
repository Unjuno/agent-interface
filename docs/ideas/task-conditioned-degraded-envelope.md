# Task-conditioned envelopes for joint capability loss

Issue #8586 proposes a task-conditioned decision boundary for combinations of unavailable or degraded capabilities. Its finite-model results test whether this contract adds value beyond composing individually eligible fallback edges; they do not establish production failure rates or live-control safety.

## Task-conditioned degraded configuration envelope — #8586

- **Status:** open; A01 and A02 report `PASS_METHOD_SCOPED` on authored finite models; independent integration remains pending.
- **Source:** [Issue #8586](https://github.com/Unjuno/agent-interface/issues/8586); [A01 evidence PR #8734](https://github.com/Unjuno/agent-interface/pull/8734); [A02 evidence PR #8738](https://github.com/Unjuno/agent-interface/pull/8738).
- **Idea:** Key an operating envelope by task class, exact joint-loss set, context, and expiry. Each entry specifies mandatory task obligations, the permitted continuation/qualified alternate/stop decision, compensating checks and their authorized performers, prohibited effects, expiry, provenance, and invalidation conditions. Unlisted combinations, stale envelopes, changed intent, unknown causes, or unavailable compensating checks resolve to `UNKNOWN`/`STOP`; single-loss fallback edges do not grant permission for a joint loss.
- **Outcome:** A01 enumerated 1,152 task/capability/context rows. Its raw-only audit reconstructed all rows with zero errors; edge-wise fallback composition made two unsupported continuations under joint loss of semantic targeting and native effect checking, while blanket stop rejected 107 feasible rows. A02 was a separately frozen, additive allocation, not a rerun or pooled extension of A01: it added a second distinct joint-loss configuration for a focused-window task. Its auditor reconstructed 336/336 rows with zero errors and decision mismatches, found two distinct edge-wise false continuations, and found zero TDCE false continuations or false stops over feasible rows; blanket stop rejected 36 feasible rows. These results are limited to the authored finite models and specified comparator policies. No GUI, model, OS input, external effect, live safety, or product benefit was tested. PR #8734 is OPEN/DIRTY and PR #8738 is OPEN/UNSTABLE; neither result is integrated.

## Relation to neighboring work

#8586 is a task-eligibility layer over capability discovery (#40), not a replacement API. It differs from route-portfolio comparison (#6278), which concerns partial-overlap route portfolios, and from assume-guarantee composition (#5328), which may subsume the proposal if it covers task-conditioned joint failures, compensations, and expiry. Keep this proposal separate until that overlap is resolved by review.
