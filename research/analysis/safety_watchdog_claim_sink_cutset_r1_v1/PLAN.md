# #1893 — typed claim-sink cut-set transfer

Task `SAFETY-WATCHDOG-CLAIM-SINK-CUTSET-R1-20260919-001`.

## H/T/D/C/U

H: exact retained #827 source must be interpreted with separate claim sinks. `RELEASE_VERIFIED` precedes all journal/ordinary-pipe work; candidate durable local receipt is independent of ordinary-pipe progress but not journal availability; parent `REPUBLISHED_RECEIPT` is only created after the ordinary data-recovery/drain phase; `pipe_only` has no local durable/recovered evidence branch.

T: byte-pin the three exact main blobs, parse unique AST/source anchors, build separate dependency graphs, apply #1882 theorem, independently reparse/audit, and reject four source-order/scope corruptions. One formal invocation only after GitHub source freeze. No X11 rerun.

D: `PASS_WATCHDOG_TYPED_SINK_CUTSET_SCOPED` iff source hashes, source-order facts, five graph classifications, theorem/direct reachability, independent audit, mutation controls, and source integrity all pass.

C: static Python source can omit scheduling, library, kernel, X-server and filesystem dependencies.

U: edge completeness outside explicit Python control flow is unknown. No statistical or hard-real-time claim.

## Expected typed classifications

1. release vs post-release DATA/evidence vertices: arbitrary-failure reachability PASS / no DATA-only cut;
2. durable local receipt vs ordinary-pipe/recovery only: PASS / no DATA-only cut;
3. durable local receipt when journal is also in the fault set: FAIL / minimum cut 1;
4. republished receipt vs ordinary recovery phase: FAIL / minimum cut 1;
5. pipe-only local evidence sink: base-unreachable / minimum cut 0.

The distinction is the result: #827 supports release independence and post-release durable retention across its temporary ordinary-pipe block; it does not by itself prove an always-republished receipt under a permanently unavailable recovery phase.
