# #1872 Fresh belief recommit epoch prevents ABA action revival

H: every successful belief COMMIT/RECOMMIT creates a fresh non-reused commit identity. Prepared action receipts bind the commit identity they observed. Reusing an opaque commit ID after invalidation/recommit can revive a stale pre-invalidation receipt when the claim returns to an equivalent state.
T: finite state machine over observe/validate/commit/prepare/invalidate/reobserve/action/contradict; weighted-state DP through depth9; fresh-epoch candidate + separate oracle + reused-ID comparator; independent tuple-state auditor.
D: candidate/oracle mismatch0; old prepared receipt admission after later recommit0; stale/contradicted action0; fresh current receipt admissions>0; successful commit epochs strictly increase; archived old commit witnesses>0; reused-ID comparator ABA admissions>0; formal1/reruns0.
C: commit identity may be compound rather than integer; wrap/reuse, distributed commit, multi-claim atomicity outside scope.
U: analytical identity/currentness prerequisite only; no runtime/model/GUI/task/token/latency/product claim.
