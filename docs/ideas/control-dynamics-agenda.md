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
