# #1702 Evidence-dependent compute decision lattice

Decision: **PASS_EVIDENCE_COMPUTE_DECISION_LATTICE_SCOPED**

This result composes the completed analytical layers under parent #1663 without allowing one layer to override another.

## Ordered lattice

### CACHED_COMPLETE

1. Dependency-version vector mismatches current evidence -> `REBUILD_REQUIRED`.
   - The stale cached result is not reused.
   - `REBUILD_REQUIRED` does not directly RUN anything; a newly instantiated current-version job must re-enter the active-job gate.
2. Exact dependency match but current time is past the usefulness deadline -> `DROP_EXPIRED`.
3. Exact dependency match and unexpired usefulness -> `REUSE`.

### ACTIVE_JOB

1. Dependency mismatch -> `CANCEL_STALE`.
2. Exact dependency match but remaining work misses deadline (`t+c>d`) -> `CANCEL_TARDY`.
3. Exact current and timely -> apply the #1695 expected-cost selector, yielding `RUN`, `WAIT`, or `TIE`.

Thus semantic reuse validity, temporal feasibility, and economic optimization are ordered rather than pooled.

## Exact finite result

The formal state space contains 22,500 typed rows:
- REBUILD_REQUIRED: 5,625
- REUSE: 3,375
- DROP_EXPIRED: 2,250
- CANCEL_STALE: 5,625
- CANCEL_TARDY: 4,050
- RUN: 595
- WAIT: 595
- TIE: 385

Candidate/oracle mismatch: 0.
Invalid reuse: 0.
Invalid rebuild-required classification: 0.
Hard-gate override: 0.
Active expected-selector mismatch: 0.
REBUILD_REQUIRED direct RUN/WAIT bypass: 0.
Unknown dispositions: 0.

Five corruption controls and the independent audit pass. Formal invocation1; reruns/replacements/tuning0.

## Scope boundary

The exact dependency-match predicate inherits #1675's assumptions: complete declared dependencies, semantic version identity, deterministic/pure result where applicable. This lattice does not calibrate the #1695 probability/cost inputs, optimize REBUILD cost, schedule multiple jobs/resources, or model partial/preemptive work. It is a typed composition contract, not a production scheduler performance claim.
