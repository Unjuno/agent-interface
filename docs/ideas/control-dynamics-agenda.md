# Control dynamics and route recovery

These open Issues ask distinct questions about what the controller can infer and when a route is useful. Finite or synthetic method results below do not establish real-time, GUI, or gameplay benefit.

## Disturbance-timescale route comparison — #6604

- **Status:** unverified transfer hypothesis; T0 method validated.
- **Source:** [Issue #6604](https://github.com/Unjuno/agent-interface/issues/6604); [retained T0 report](../../research/analysis/disturbance_timescale_6604_t0_v1/REPORT.md); [T1 trace prescreen](../../research/analysis/disturbance_timescale_6604_t1_eligibility_20261002/REPORT.md).
- **Idea:** Compare direct and bounded local-feedback routes by declared disturbance timescale, so a pooled score cannot hide a route-by-stratum crossover.
- **Outcome:** Successor T0 allocation 02 returned `PASS_METHOD_SCOPED`: a separate raw-only audit reconstructed 14 synthetic rows and the planted slow/fast crossover and no-crossover control. The pooled score selected direct despite the local route winning the slow stratum. A read-only T1 prescreen returned `HOLD_NO_ELIGIBLE_TRACE`; retained MAP01 traces lack an exogenous disturbance schedule and do not support this route-by-timescale estimate. The later logical-time-scaling refinement remains unrun. No real controller, GUI, DOOM, latency, or safety result follows.

## Source-supported path-class switching — #6586

- **Status:** unverified transfer hypothesis; initial T0 method validated, later duplicate allocation showed no incremental value in its fixture.
- **Source:** [Issue #6586](https://github.com/Unjuno/agent-interface/issues/6586); [merged T0 evidence PR #6602](https://github.com/Unjuno/agent-interface/pull/6602); [retained later A01 package](../../research/analysis/bounded_path_class_switching_6586_t0_20261002/README.md); [open representation-boundary PR #8271](https://github.com/Unjuno/agent-interface/pull/8271).
- **Idea:** After a bounded no-progress condition, switch only when current source-visible evidence supports a distinct safe path class; otherwise retain `UNKNOWN_CLASS` and use ordinary fallback or yield.
- **Outcome:** The first retained allocation's auditor found 15 missing terminal-action errors and remains `FAIL_OR_HOLD`; it is preserved unchanged in the [A01 package](../../research/analysis/bounded_path_class_switching_6586_t0_20261002/README.md). The merged successor T0 PR #6602 returned `PASS_METHOD_SCOPED` on its distinct authored blocked-route fixture. A separate 2026-10-07 A01 audit found all three arms tied at 7/12 actions in one blocked-edge case; post-run review identified overlap with #6602, so it was classified `NO_INCREMENTAL_VALUE_A01`, not a replication or replacement. Draft PR #8271 separately returned `PASS_REPRESENTATION_BOUNDARY_SCOPED` for finite winding-vector collision controls. It tests representation only; no route-policy, visual perception, GUI, or DOOM benefit is established.

## Reset-qualified trial-to-trial residual learning — #8661

- **Status:** open; retain a method HOLD despite favorable synthetic diagnostics.
- **Source:** [Issue #8661](https://github.com/Unjuno/agent-interface/issues/8661); open evidence [PR #8722](https://github.com/Unjuno/agent-interface/pull/8722).
- **Idea:** Test whether low-dimensional residual updates improve one bounded repeated-control task only after an independently valid terminal outcome, with reset/generation qualification and a fixed-control fallback outside the initial-state envelope.
- **Outcome:** T0 A01 candidate and auditor each ran once with zero retries. The initial auditor reported `PASS_METHOD_SCOPED`, held-out median pre-correction error 0.010 versus 0.6495 and correction median 0 versus 1, with no hard-gate regressions and 5/5 mutations reported detected. Post-result code review found `candidate.py` computes `terminal_verified` itself and uses it to authorize updates; no independent verifier receipt enters the update path. The disposition is therefore `HOLD_CANDIDATE_SELF_CERTIFIES_TERMINAL`. Preserve metrics as synthetic diagnostics only; no candidate rerun, live GUI/model/runtime or task-success claim. PR #8722 is OPEN/DIRTY and not integrated.

## Phase-dependent controllability under interface delays — #8668

- **Status:** open; A01 `FAIL_HARNESS` invalidated, A02 `PASS_METHOD_SCOPED` on the authored finite plant; independent review and integration remain pending.
- **Source:** [Issue #8668](https://github.com/Unjuno/agent-interface/issues/8668); [A01 correction PR #8698](https://github.com/Unjuno/agent-interface/pull/8698); [A02 result PR #8745](https://github.com/Unjuno/agent-interface/pull/8745).
- **Idea:** Test whether a logical interface operation's controllability changes across proposal, admission, queue, emission, consumption, and effect-acknowledgement phases when control and observation messages can be delayed or reordered.
- **Outcome:** A01's reported static-policy contrast was withdrawn after a read-only consistency check found 228/481 counterfactual rows reused a plant already changed by cancellation; no rerun was made. The separately frozen A02 computed each policy action against the same 481 exogenous schedules: its authored optimistic static-cancelable comparator made 102 false cancellation claims and admitted 51 unsafe duplicate retries, while static-uncontrollable and fail-closed comparators each missed 114/114 safe removals. The phase-refined arm preserved 228/228 modeled safe removals with zero false cancellations or unsafe duplicates, and the raw-only auditor rejected all five mutations. These are finite-model results for the specified comparator policies only. Real backend phase observability, delay bounds, GUI effects, product safety, and task benefit remain unverified. Both PRs remain Draft; #8698 is CLEAN and #8745 is DIRTY, so neither result is integrated.
