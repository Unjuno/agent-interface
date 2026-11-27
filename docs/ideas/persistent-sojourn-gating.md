# Persistence-gated optional-work throttling — #6650

- **Canonical source:** Open [Issue #6650](https://github.com/Unjuno/agent-interface/issues/6650), an offline flow-control method question. Merged [PR #6670](https://github.com/Unjuno/agent-interface/pull/6670) retains the original T0; merged [PR #6673](https://github.com/Unjuno/agent-interface/pull/6673) adds a serialization correction without rerunning the candidate or auditor.
- **Hypothesis:** Use persistent queue residence, rather than instantaneous queue length, to suppress generation of redundant optional observations/probes while retaining already admitted records and all mandatory safety/currentness/effect work.
- **Result:** T0 `FAIL_HYPOTHESIS` on nine fixed synthetic traces / 63 offered IDs. Age-persistence reduced stale optional deliveries from fixed generation's 13 to 6 on sustained overload, but queue-length reduced them to 3, violating the frozen comparison. Do not tune or rerun that allocation.

## Evidence and audit boundary

On the sustained-overload trace, stale optional deliveries were 13 (fixed), 3 (queue-length), and 6 (age-persistence). Across all nine traces, raw-state reconstruction counted 11 queue-length tier transitions and 16 age-persistence transitions; this is descriptive, not an independent replay of the controller law. Age-persistence avoided throttling the transient burst and entered during a zero-dequeue blackout, but those scoped properties do not offset its adverse primary comparison. Mandatory IDs and terminal outcomes matched fixed generation across policies.

The raw accounting auditor reconstructed offered IDs, suppressions, service records, generations, sojourns, freshness terminals and mandatory coverage with zero errors. It did **not** independently replay the full controller transition law. The primary hypothesis failure remains the reported frozen comparison; the audit limitation narrows claims about implementation conformance. The later strict-JSON correction preserved the original malformed `AUDIT.json` and added `AUDIT_CORRECTED.json`; no experiment process was rerun. See the [formal report](../../research/analysis/persistence_gated_throttle_6650_t0_v1/REPORT.md) and [correction-only replay package](../../research/analysis/persistence_gated_throttle_6650_control_replay_20261002_01/REPORT.md).

## Boundaries and related work

This is a producer-side throttle proposal, not queue eviction, deadline scheduling, AoI selection, an event-drop policy or a runtime scheduler. It tests persistence-gated suppression of explicitly optional request generation; mandatory evidence and already-admitted requests retain their normal semantics. The synthetic study does not measure real queues, planner decisions, task correctness, user benefit, latency, resource cost, shared-service interactions or safety.

Closed [#8891](https://github.com/Unjuno/agent-interface/issues/8891) contributes a recent-minimum sojourn estimator as a candidate refinement within #6650; it is not an independent experiment or replication. [#8494](https://github.com/Unjuno/agent-interface/issues/8494) concerns synchronization among session-local controllers, while [#8916](https://github.com/Unjuno/agent-interface/issues/8916) studies preventive producer pacing for synchronized bursts. Keep those estimands separate.
