# EVIDENCE-DEPENDENT-COMPUTE-SCHEDULER-DOMINANCE-R0

Issue #1687. Exact-rational analytical rung only.

Frozen contract:
- dependency currentness is boolean;
- current time t, remaining deterministic compute c>=0, hard inclusive deadline d are exact Fractions;
- stale-source publication is forbidden;
- result has zero usefulness after d;
- no partial-result value;
- REUSE is out of scope and must never be selected.

Candidate hard gate: RUN is feasible exactly when dependencies are current and t+c<=d.

Formal state grid:
- t in {0, 1/2, 1, 3/2, 2};
- c in {0, 1/4, 1/2, 1, 3/2, 2};
- d in {0, 1/2, 1, 3/2, 2, 5/2, 3, 4};
- currentness in {current, stale}.

Paired-future witness uses identical current metadata t=0,c=1,d=2,current=true.
RUN begins now. WAIT delays 1/2 and rechecks currentness/hard feasibility.
STABLE: no invalidation. INVALIDATE_SOON: dependency invalidates at 1/4.
Cost = fixed no-result penalty 10 when no useful result + useful-completion latency when useful + wasted compute.
The fixed no-result penalty is common inside a future and does not create the preference reversal.

Decision gate is exactly Issue #1687. One formal invocation, reruns/replacements/tuning0.
