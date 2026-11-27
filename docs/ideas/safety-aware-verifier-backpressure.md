# Safety-aware backpressure for verifier pipelines — #5372

- **Source:** Open [Issue #5372](https://github.com/Unjuno/agent-interface/issues/5372), an offline queueing and flow-control question across observation, verification, evidence reduction, escalation, and action.
- **Claim boundary:** The checked-in evidence contains distinct synthetic counterexamples and scoped mechanism results. It does not show that the current runtime has queue collapse or that a production backpressure policy would improve task outcomes.

## Results that must remain separate

### Endogenous verification demand — T1

Allocation 01 is preserved as `STOP_HARNESS_IMAGE_IDENTITY_STRING_MISMATCH`; its candidate did not start and it was not retried. Separate allocation 02 reported `PASS_SCOPED_COUNTEREXAMPLE` for its finite model. Under the fixed high offered load, BASE/FIFO verified 10 tasks by the horizon, FAST/FIFO verified 4, and FAST/BACKPRESSURE verified 14. Stale attempts were 50, 64, and 13 respectively; the backpressure arm also had 13 retries and zero UNKNOWN tasks after drain. All six mandatory safety events were serviced in every cell. The equal-offer fixed schedule is the primary contrast; the completion-triggered closed-loop source offered 36 tasks under FAST/FIFO and 21 under FAST/BACKPRESSURE, so those counts are not an equal-arrival comparison. The selected-survivor p95 is not an independent pass gate.

This supports only a counterexample in an authored deterministic queue model. It does not test the broader FIFO/deadline and priority-only comparator set described in #5372 or a deployed verifier. See the [T1 allocation 02 report](../../research/analysis/safety_backpressure_5372_t1_successor_20261001/REPORT.md) and preserved [allocation 01 STOP](../../research/analysis/safety_backpressure_5372_t1_v1/STOP.json).

### Optional-route expansion — separate T0

The route-expansion fixture reported `PASS_METHOD_SCOPED`: on six simultaneous tasks, BASE_ONLY used 12 local ticks and verified 5/6 by the horizon; EXPANDED_GREEDY used 6 ticks but verified 3/6; EXPANDED_PRESSURE used 11 ticks and returned to 5/6. All three mandatory safety events were served in each arm. This is a six-task authored counterexample to local-cost-only route selection, not evidence of a live backpressure controller or a general optimal policy. The [route-expansion report](../../research/analysis/backpressure_route_expansion_5372_a01_20261003/REPORT.md) retains its exact scope.

### Telemetry faults and an authoritative cap — separate finite analysis

In the atomic single-owner unit-job model, `SUBSUMED_BY_AUTHORITATIVE_CAP_SCOPED`: a hard pending-work cap was sufficient and delayed/faulty telemetry added no completion advantage. Across 6,561 enumerated conditions, cap-only completed 22,797 synthetic jobs with zero cap violations, while report-only had 2,251 violating cases. The report's independently coded reference reconstructed the event accounting and rejected six value-changing controls. This does not justify a sophisticated runtime policy: atomic reservation is assumed, and the model omits distributed ownership, heterogeneous jobs, deadlines, retries, and occupied in-flight server slots. See the [telemetry-cap report](../../research/analysis/backpressure_5372_telemetry_cap_20261003_api/REPORT.md).

## Remaining decision boundary

The latest Issue note identifies the unresolved transfer question as the actual verifier path's workload contract: which work is externally offered, becomes ready from a dependency, or is policy-optional? These must not be inferred from observed latency. A read-only qualification would bind work identity, predecessor, readiness/release/arrival, queued and in-flight reservation, terminal/cancel/UNKNOWN state, and session identity; unknown origins stay UNKNOWN. No workload-origin audit has been recorded as an integrated runtime result.

Keep neighboring questions distinct: #6650 studies persistence-gated optional request generation; #8494 studies synchronization between session-local controllers sharing delayed feedback; #8916 studies preventive smoothing of synchronized producer bursts; #5702 studies endogenous choice/task-mix change. None is a duplicate replication of the #5372 allocations above. No result here establishes runtime queue stability, GUI/model behavior, human benefit, fairness, safety guarantees, or production throughput.
