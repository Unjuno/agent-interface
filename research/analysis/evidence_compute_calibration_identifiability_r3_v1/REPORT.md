# #1725 Evidence-compute calibration identifiability

Decision: **PASS_RETAINED_EVIDENCE_COMPUTE_CALIBRATION_NOT_IDENTIFIABLE_SCOPED**

## Required calibration contract

A concrete #1702 job class needs same-population evidence for:
- empirical invalidation probability/incidence p over a declared horizon;
- stable-world WAIT loss g;
- invalidation-world obsolete RUN loss w in the same cost unit;
- exact-version reuse_rate under the #1675 predicate;
- version-maintenance/check cost;
- one job/population identity tying the quantities together.

Seven retained families were audited. Fully calibratable same-population families: **0**.

## Why the strongest candidates still do not calibrate #1702

- **#1583 O3 relevance generation**: 200,000 exact histories and 40,000 stale-shift cases prove currentness semantics, but the family counts are authored corpus composition. They are not a deployment invalidation probability and contain no WAIT/waste/reuse/version-cost measurement.
- **#972 target pre-input revalidation**: 16 real private-X11 sessions measure a 1.586 ms median added capture and reproduce stable/swap outcomes. The 2x2 state/policy matrix is authored; capture latency is not stable-world WAIT loss for a background compute job.
- **Adaptive acquisition caller v1**: has zero-call warm reuse and one-call invalidate/repair branches, but the retained document explicitly labels them test-double mechanics and says they do not demonstrate cost/latency improvement.
- **#1688 phase overlap**: measures a 150.316 ms median controlled effect-tail overlap gain and a shared-resource conflict. This is a different scheduling mechanism; its wall gain is not g for a versioned compute job and its wrong visible effect is not obsolete-compute w.
- **#1179 current-evidence guard cost**: measures 0.025028 ms median AF_UNIX acquisition+validation and invalidation-to-refusal timing, but for a 57-byte action-guard record. It cannot be substituted as dependency-version maintenance cost for an unrelated background computation.
- **#1675 reuse theorem**: defines exact-version reuse safety under explicit assumptions, but intentionally provides no empirical reuse rate or cost.
- **Integrated efficiency fixed sequence**: the persistent arm has cold1/reuse4/repair1 across six exact tasks with real tokens/wall. That is a fixed preregistered sequence, not a sampled background-job population. Its route frequencies cannot be promoted to generic p or reuse_rate, and task elapsed differences do not isolate g or w.

## Integrity

Construction and the single formal invocation both found zero calibratable families. Six corruption controls reject the tempting evidence-role substitutions:
1. authored stale fraction -> empirical p;
2. test-double reuse branch -> empirical reuse_rate;
3. phase-overlap wall gain -> compute-job g;
4. action-guard cost -> another job's version-maintenance cost;
5. fixed-sequence route frequency -> generic reuse rate;
6. cross-family union -> one calibrated job population.

Independent audit PASS. Formal invocation1; reruns/replacements/tuning0. No production estimate or scheduler recommendation was emitted.

## Next legal rung

Do not mine additional unmatched retained traces. Prospectively freeze one concrete deterministic background job, one explicit workload distribution, one dependency-version representation and one commensurate cost function. Measure p/g/w/reuse_rate/version_cost in that single population. The result will calibrate only that declared workload/job class, not deployment generally.
