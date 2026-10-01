# #1737 Prospective evidence-compute calibration fixture — retained first outcome

Decision: **FAIL_INTEGRITY — audit corruption binding gap.** Scientific promotion: **NONE**.

The first and only frozen formal allocation completed its 64 matched active scenarios, 64 cache requests and 240,000 version checks. The raw mechanics are promising but are not promoted because the preregistered independent audit failed one mandatory corruption control.

## First formal mechanics retained without reclassification

- active scenarios: 64 = 48 STABLE + 16 INVALIDATE;
- executions: 128/128 final current-version digest correct;
- stale old-version publications: 0;
- invalidated RUN old jobs aborted: 16/16;
- invalidated RUN positive obsolete CPU: 16/16;
- workload invalidation incidence: 16/64 = 1/4 by frozen schedule;
- cache dispositions: 48 REUSE / 8 REBUILD_REQUIRED / 8 DROP_EXPIRED;
- fixture reuse rate: 48/64 = 3/4 by frozen request mix;
- version-check benchmark: 240,000 rows, p50 90 ns, p95 100 ns, max 253,594 ns;
- stable conditional loss sum g: 240,512,261 ns across 48;
- invalidation conditional loss sum w: 76,075,399 ns across 16;
- direct RUN-minus-WAIT aggregate cost: -164,436,862 ns;
- exact accounting identity `RUN-WAIT = w_sum-g_sum` holds in the retained result.

These values are descriptive retained evidence only because the audit integrity gate failed.

## Integrity failure

The audit included five corruption controls. Four were rejected correctly. The `double_count_obsolete_rejected` control failed: mutating an invalidated RUN row by adding `obsolete_cpu_ns` a second time to its stored `cost_ns` changed both the auditor's recomputed `w_sum` and aggregate cost consistently, so the existing auditor did not independently reconstruct the declared formula

`cost_ns = completion_wall_ns + obsolete_cpu_ns`.

Therefore a corrupted row could remain internally self-consistent under the auditor. This is a result-binding defect, not permission to accept the formal measurements.

The first formal invocation is consumed. No rerun, replacement or threshold change is allowed under this Issue. The exact raw first outcome is retained losslessly as deterministic gzip+base64 with a restore hash check.

## Next legal successor

A separately preregistered retained-evidence audit may use this exact frozen `RAW.json` only. It must independently recompute every row's declared cost from primitive `completion_wall_ns` and `obsolete_cpu_ns`, reject the double-count corruption, re-derive all p/g/w/cache/version summaries, and verify source/raw identity. It must not execute the job fixture again or alter the first outcome.
