# Issue #7778 T0 result

**Disposition: `PASS_METHOD_SCOPED`; `H_PASS_SCOPED` in the preregistered finite model.** The candidate and independent auditor each ran once on the frozen 18-case matrix. The auditor found 0 errors across 108 policy/overhead rows and 3/3 fail-closed controls. This is not a container-backed or real-time result.

## Outcome

The one-CPU integer-slot model used 32-tick horizons, static reservation `Q=2/P=8`, three policies, and per-job dispatch overhead factors 0 and 1. An independent exhaustive unit-slot scheduler found 17/18 control workloads feasible at overhead 0 and 12/18 at overhead 1. Across both factors, the guarded policy missed no control deadline on any workload the exhaustive oracle classified feasible. All seven infeasible model/factor combinations are listed in `result/audit.json` with an overload-demand interval; their misses are not counted as safety successes.

On the frozen positive-slack subset (8 cases, overhead 0), guarded slack executed **222** best-effort payload units versus **192** for static reservation: **+30 units (+15.625%)**. This crosses the preregistered hypothesis threshold. Across the full overhead-0 matrix, guarded slack executed 475 payload units, static reservation 432, and priority-only 502. Thus the scoped comparison supports reclamation relative to the deliberately non-borrowing fixed reservation, but does **not** show an advantage over the simpler priority-only policy; priority-only matched the guarded policy's no-miss result on feasible cases while executing more best-effort payload. No scheduler promotion is warranted from this finite result.

The fixed `exact-boundary` control is feasible at overhead 0. The `joint-infeasible` control is infeasible at overhead 0 with demand 2 in capacity 1 over `[8,9)`. At overhead 1, additional infeasible cases include the boundary bursts; their independent overload witnesses and per-policy misses remain in the audit output. Dispatch overhead is a discrete one-unit-per-job-start sensitivity, not measured machine overhead.

## Evidence and execution

- Frozen base: `a38c61334ff5dbd7d17269467c26f74e9ad4a84f`; preregistered on Issue #7778 before formal execution (comment ID `5984217471`). Freeze manifest SHA-256: `e77e3590a485b14e19ebda71801d7a4049b4e7d2643ec4236a2226540164756b`.
- Candidate: 108 raw rows (18 cases × 3 policies × 2 overhead values), one process invocation, exit 0. Raw JSONL SHA-256: `2732eee44e98f786e3df48d57e3973e3845dce45571301716a0041f71062c50c`.
- Independent auditor: one process invocation, exit 0; 0 audit errors, `PASS_METHOD_SCOPED`, `H_PASS_SCOPED`. Audit JSON SHA-256: `3bdb8b85d5ca5eff922bf6a067f1f16d359650b7a7f567049b7d09113dd21da1`.
- Construction tests: 7/7 passed before freeze/formal execution. They cover exact demand, jointly infeasible demand, job-class/WCET/preemption refusal, release-order non-leakage, reservation counters, and mutations for omitted obligations, duplicate slots, false completion, early replenishment, and invalid class.
- The retained raw-only audit implements its own finite schedule enumerator and does not import `candidate.py`. `result/RESULT.json`, both receipts, `result/refusals.json`, captured stdout, and `SHA256SUMS` preserve the complete record.
- OrbStack returned daemon info but image listing/inspection failed on the content-store blob with `operation not supported`. No container ran; repeated Docker access stopped. As this arithmetic-only method uses no container feature and makes no timing/isolation claim, the frozen fallback was host CPython 3.14.5 on ARM64. CI's Python 3.12 run remains a separate gate.

## Scope boundary

The evidence supports only this finite synthetic scheduler-method result. It does not replay or amend #7722, reuse #7748/#7762 rows as fresh trials, prove universal schedulability beyond the enumerated release envelope, measure dispatch cost, establish host/OS/cgroup/OrbStack enforcement, explain actual release latency, or demonstrate GUI/key-up/physical-release safety or product performance. The result suggests the next scientific comparison should preserve priority-only as the simple baseline; no runtime change is proposed here.
