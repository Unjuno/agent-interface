# Task risk semantics and sequential decisions

This agenda connects the task-level risk posture in [Issue #26](https://github.com/Unjuno/agent-interface/issues/26) with its distinct, open successor [Issue #8908](https://github.com/Unjuno/agent-interface/issues/8908). Neither issue is closed, and no production or safety result is claimed.

## Distinct questions

| Question | Existing record | Remaining question |
|---|---|---|
| Task-level risk posture | #26 proposes hard forbidden-effect constraints plus bounded ambiguity, probes, recoveries, verification and escalation. | Can a declared posture change bounded continuation while preserving hard invariants and universal fallback? The original issue's Calc/drag experiment has no result recorded here. |
| Within-task dynamic consistency | #8908 proposes an exact finite two-stage comparison between an ex-ante static terminal-risk policy and re-optimization of the same criterion at a reachable information node; a nested conditional criterion is a comparison. | Can the frozen tree witness a genuine preference reversal under identical conditional inputs, separate from Bayesian updating anticipated ex ante? No experiment or implementation is recorded. |
| Trajectory exposure composition | A #26 addendum proposes a separate optional probabilistic mission budget for composing per-opportunity soft-risk upper bounds. | Calibration and dependence conditions remain unresolved; the addendum is a proposal, not evidence that GUI risk probabilities are valid. |

These questions are related but not interchangeable. #8908 concerns temporal semantics of a risk criterion and policy re-optimization; the #26 addendum concerns whether several soft-risk opportunities fit within one total bound. Both keep authority, release, and forbidden effects outside any tradable budget. They differ from #5424 action-class burn/freeze, #5380 probabilistic authority-property checking, #5315/#7993 verifier calibration, and #6269 trajectory diagnostics.

## Evidence and limits

No repository-specific experiment, solver result, calibrated risk estimate, or runtime policy change is recorded for #8908. The cited literature establishes prior work on time-consistent risk measures; it does not validate an Agent Interface policy:

- De Lara and Leclère, [Building up time-consistency for risk measures and dynamic optimization](https://doi.org/10.1016/j.ejor.2015.08.058).
- Pichler and Shapiro, [Risk Averse Stochastic Programming: Time Consistency and Optimal Stopping](https://arxiv.org/abs/1808.10807).

A finite witness can establish only a scoped mathematical-method result. It cannot establish calibrated real-world risk, safe GUI behavior, task success, or authority to act.

## Next finite test

If selected, freeze a tiny two-stage tree, exact rational probabilities/losses, static criterion, nested criterion, hard-forbidden outcomes, tie-breaking, and reachable information node before solving. An independent exhaustive checker should reconstruct all policies and values. Include expectation/no-information controls and require the ex-ante continuation and conditional re-solve to use identical conditional inputs. A no-witness result applies only to that frozen case. This test needs no model, GUI, container, or shared runtime.
