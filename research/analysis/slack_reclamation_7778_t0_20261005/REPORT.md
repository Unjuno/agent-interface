# Issue #7778 T0 result

**Disposition:** PASS_METHOD_SCOPED; **hypothesis:** H_PASS_SCOPED.

The frozen candidate, deterministic workload generator, and independent auditor
each ran once in the pinned WSLc Python 3.12.15 image with network disabled,
read-only source, separate writable output, and no retries. The auditor
exhaustively enumerated integer-slot schedules for nine traces. It checked 27
policy rows with zero audit errors and rejected all six frozen raw-log
mutations.

On the four preregistered positive-slack traces, demand-guarded slack stealing
completed 21, 22, 22, and 21 optional service units. Static reservation
completed 18, 18, 18, and 9. Every slack-stealing result met every hard control
deadline and matched the independent oracle's maximum optional service. The
service gain was 3, 4, 4, and 12 units respectively.

The exact-demand-boundary and burst traces show a limitation of the static
comparator: it returned UNKNOWN_OVERLOAD after a control deadline miss in
each. The slack policy met all hard deadlines in both. The deliberately
infeasible joint-demand trace returned UNKNOWN_OVERLOAD; the auditor's exact
oracle confirmed infeasibility. Unknown WCET and non-preemptive cases returned
HOLD_MODEL_MISMATCH; the invalid job class returned HOLD_INVALID_JOB_CLASS,
all before scheduling actions.

The auditor independently checked release/deadline accounting, reservation
phase, per-tick single-service capacity, released-job eligibility, hard
deadlines, and the slack guard against every allowed future control-release
sequence. It also computed the maximum optional service under the finite
trace. Dropped/duplicated ticks, omitted/forged arrivals, double service,
early reservation, and an unreleased control action were all rejected.

## Scope

This supports only the declared finite, preemptive, single-processor,
integer-time simulator. It does not establish that WCET or sporadic-arrival
contracts are knowable for real control work, or that reclaiming optional CPU
work improves WSL/Linux scheduling, input-release latency, GUI correctness,
physical key release, safety, or end-to-end task performance. The host reported
that swap/cgroup memory limits are unavailable; no resource enforcement or
timing benefit is claimed. No GPU was used because this exact small
CPU-scheduling enumeration has no GPU-dependent computation.

Raw input, candidate output, audit, and reproduction record are retained under
formal_01/; their hashes and the frozen source hashes are in SHA256SUMS and
FREEZE.json.

## Remaining Issue-level gate

This allocation froze dispatch overhead at zero. Issue #7778's proposed T0
also calls for scheduler/dispatch overhead as a frozen sensitivity factor;
that dimension was omitted from this allocation. Therefore the PASS labels
above apply only to the explicitly frozen zero-overhead synthetic method
scope. They do not complete Issue #7778's full T0 or authorize closing it.
A separate additive allocation must test overhead sensitivity without
reusing or changing these raw results.
