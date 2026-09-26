# Runtime evidence-compute lattice transfer (#2766)

## Disposition

**HOLD_RUNTIME_INPUTS_INCOMPLETE** (audit-control subtype: **HOLD_EVIDENCE_AUDIT_INCOMPLETE**).

The 18/18 runtime cases complete and the separately structured raw-ledger oracle reports zero errors over 23 decision points. However, the frozen formal PASS gate also required all 12 copied-evidence corruptions to be rejected. The frozen controls reject only 10/12, so this allocation is not promoted to PASS and is not rerun.

## H / T / D / C / U

**H.** The unchanged #1702 ordering can consume a real source-versioned PNG capture/local-compute ledger without stale reuse, hard-gate override, implicit rebuild execution, or reusable publication after cancellation.

**T.** Eighteen fixed cases over CACHED_COMPLETE, ACTIVE_JOB and measured rebuild. Actual operations include stdlib PNG encoding/decoding, SHA-256, atomic filesystem source-version mutation, monotonic capture/compute/deadline clocks, measured compute/wait costs, explicit invalidation probes, partial compute and cancellation. Two immutable nine-case formal batches, each invoked once.

**D.** Runtime rows meet the decision/oracle and policy-enforcement gates: 18 cases, 23 decisions, errors=[], stale/tardy publication0, missing required partial0. Formal PASS is withheld because copied-evidence controls are10/12 rather than12/12. No stale reuse, tardy publication, hard-gate override or REBUILD_REQUIRED->RUN bypass was observed in formal rows, so this is not FAIL_POLICY_ENFORCEMENT.

**C.** Python/filesystem/PNG/zlib scheduling and authored invalidation probes affect absolute timing. Diagnostic p/g/w calibration is not a deployment probability. The two failed mutation controls are control-design defects: wrong_g remains mathematically RUN in its selected low-p case; publish_after_cancel mutates a RUN case with no later cancel.

**U.** No model/task utility, GUI generality, production threshold, global scheduler optimality, cross-platform timing or token benefit. #2806 remains the prospective deployment calibration question.

## Exact runtime result

Decision-point counts: REUSE2, DROP_EXPIRED1, REBUILD_REQUIRED5, RUN6, WAIT1, TIE2, CANCEL_STALE4, CANCEL_TARDY2.

Directed controls show cached mismatch dominates expiry; stale/tardy active jobs stop before expected-value selection; capture/compute invalidation and deadline crossing cannot publish reusable results; partial compute is retained but not reused; measured rebuild enters a distinct fresh ACTIVE_JOB; the no-implicit-run rebuild control stops at REBUILD_REQUIRED.

## Preserved preformal incidents

1. Initial unittest invocation failed because the working directory was not on the module search path; formal0. Corrected invocation only changed how tests were launched.
2. First public premeasurement snapshot was byte-exact but static review found cached_reuse_at_deadline had a 50ms margin. Before formal0 changed, the fixture was corrected to exact t==deadline and a regression test added. The earlier snapshot remains in branch history.
3. A local patch helper for that correction first raised a quoting SyntaxError before writing source.

## Reproduction / evidence

Do not rerun the consumed formal allocation. Restore the data-only evidence capsule, verify the manifest, then run only the raw auditor/tests on a fresh copy. All original formal PNG/source/result/receipt files, batch receipts, construction outputs, frozen source, audit and failed corruption-control result are retained.
