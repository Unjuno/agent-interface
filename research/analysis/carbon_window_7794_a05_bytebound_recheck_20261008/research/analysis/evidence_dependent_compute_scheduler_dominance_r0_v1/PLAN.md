# #1687 Hard RUN/CANCEL dominance for evidence-dependent compute

H: RUN is hard-infeasible if source dependencies are stale or t+c>d. If current and t+c<=d, hard metadata alone cannot universally choose RUN vs WAIT because paired futures with identical current metadata can reverse preference. Inclusive t+c=d is feasible. REUSE is out of scope.
T: Fraction state-space, directed controls, exhaustive current/stale x t/c/d grid, paired STABLE/INVALIDATE_SOON futures, independent auditor, corruption controls.
D: hard-feasibility mismatch0; stale accepted0; tardy accepted0; exact ties feasible; paired preference reversals>0; REUSE decisions0; formal1/reruns0.
C: no preemption/partial value/resource contention/multijob/soft deadline model.
U: analytical one-job pruning boundary only; no runtime latency/CPU/product claim.
