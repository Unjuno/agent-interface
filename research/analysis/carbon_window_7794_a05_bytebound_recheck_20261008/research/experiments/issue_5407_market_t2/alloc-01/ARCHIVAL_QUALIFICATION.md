# Archival qualification: #5407 T2 allocation-01 pre-run STOP

This is an exact preservation of a pre-execution STOP record from source branch
`research/5407-capacity-aware-reallocation-t2-20261001`, tip
`69e22cdda613bb10de8bc6b87df3a9558991c26e`. The original file's Git blob is
`456585766f2cfea8e0f072a3d251e36e8ec7ac4f`; the copy at
[`STOP.json`](STOP.json) must remain byte-identical.

## Recorded disposition

`STOP_BASE_ADVANCED_BEFORE_RUN`: preregistered base
`3f1d3b363bc61dd8cbf900627e1a32942c1d5fe4` differed from the observed main
`c3227bccfbb7f95ff950edb0d86888ed26f99ece` before invocation. Candidate/runner
invocations = 0, auditor invocations = 0, raw created = false, retry = false.
The intended response was to preserve this freeze unchanged and allocate a
distinct current-main successor.

This is not a candidate result, audit result, scientific PASS, or scientific
FAIL. No raw file is missing by accident according to the frozen STOP record;
none was created because execution never began. This archive did not run the
candidate, auditor, container, or any experiment.

## Separation from later work

The later #5407 T2b host-construction allocation is a separate package at
[`../issue_5407_market_t2b/`](../issue_5407_market_t2b/). Its recorded
scarcity-first hypothesis FAIL and raw-audit PASS do not replace or reinterpret
this pre-run STOP. The separate container reproduction remains unrun pending
its required exclusive allocation. No resource authority or rerun is implied.

This archive only republishes the original STOP bytes and qualifies their
scope. It does not change #5407's open status or the historical allocation.
