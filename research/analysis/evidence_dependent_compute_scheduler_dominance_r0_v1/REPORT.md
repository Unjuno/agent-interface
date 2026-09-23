# #1687 Evidence-dependent compute scheduler hard-dominance result

Decision: **PASS_COMPUTE_SCHEDULER_HARD_DOMINANCE_SCOPED**

## Hard pruning theorem

Under the frozen one-job contract, a background computation can produce a publishable timely result only if:

1. its declared source dependencies are still current at the scheduling decision; and
2. its deterministic remaining compute time fits the inclusive hard usefulness deadline.

Therefore RUN is hard-infeasible when dependencies are already stale or when `t + c > d`. Exact equality `t + c = d` is feasible because the deadline is explicitly inclusive.

The full Fraction grid contained 9,826 states:
- CANCEL_STALE: 4,913;
- CANCEL_TARDY: 3,944;
- RUN_FEASIBLE: 969;
- hard-feasibility mismatches: 0;
- stale RUN acceptances: 0;
- tardy RUN acceptances: 0;
- exact-deadline current rows: 153/153 feasible.

## Why feasibility does not choose RUN versus WAIT

For every hard-feasible row with nonzero remaining compute (816 rows), the analysis constructs two futures with identical current metadata.

**STABLE:** dependencies stay valid. RUN now finishes at `t+c`; a concrete WAIT policy delays start by `c/4`, so RUN completes earlier or is the only timely completion.

**INVALIDATE_SOON:** dependencies invalidate after `c/2`; a replacement computation costs `c/4`. RUN and WAIT can reach the same replacement completion time, but RUN wastes `c/2` of obsolete work while WAIT does not. WAIT therefore wins under the declared completion-plus-waste objective.

Preference reversals were constructed for 816/816 feasible nonzero rows. Consequently, currentness + remaining cost + deadline are enough to prune impossible RUNs, but not enough to universally choose RUN over WAIT for the remaining feasible region. A richer scheduler needs future invalidation likelihood, utility, resource contention, partial-value or related information.

## Scope boundary

This result does not decide REUSE; REUSE decision count is zero and the semantic reuse condition remains owned by #1675. It also does not model preemption, partial results, multiple jobs, soft deadlines, or production scheduling performance.

Independent audit and four corruption controls pass; formal invocation 1, reruns/replacements/tuning 0.
