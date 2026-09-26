# Issue #4186 result

**Decision: PASS_EFFECT_COMMIT_DEADLINE_SCOPED**

One prospectively frozen 36-case allocation completed with no reruns/replacements/post-freeze tuning. All proposal-ready and pre-dispatch timestamps were before the 120 ms task deadline.

- PRE_DISPATCH_ONLY: all six long-delay cases committed effects after the deadline (~140.4–150.6 ms).
- POSTHOC_EFFECT_CHECK: the same six late effects occurred, then were correctly labelled LATE; detection did not prevent the side effect.
- APP_COMMIT_DEADLINE: all six long-delay cases sampled the deadline immediately before commit and refused with zero effect.
- All 18 short-delay cases across the three policies produced on-time effects (~50.4–90.6 ms).

Raw-only audit: 36 rows, errors=[]; 11/11 semantic/provenance corruption controls rejected. Frozen source hashes remained unchanged. Authority was false in every row.

## H/T/D/C/U

- **H:** an on-time dispatch does not establish an effect-by-deadline contract when app processing can delay commit.
- **T:** three policies x four schedules x three repetitions, separate application subprocess, CLOCK_MONOTONIC, deadline120 ms/freshness400 ms.
- **D:** candidate late effects0, candidate valid effects6/6 short cells, comparator/posthoc late effects12/12 long cells, audit/control gates pass.
- **C:** cooperative app understands the deadline; sleep delay is directed and does not model arbitrary GUI commit hooks.
- **U:** no hard-real-time, crash/power-loss, production authority, model/task utility, GUI, token/latency-benefit, or natural-rate claim.

## Integration handoff

If task semantics require the **effect** itself before an absolute deadline, checking proposal-ready or pre-dispatch time is insufficient. Either the effect owner must enforce the deadline at commit or the system must treat a late posthoc receipt as an already-occurred violation, not as prevention. Reuse existing application/transaction semantics where available rather than inventing a universal deadline field.
