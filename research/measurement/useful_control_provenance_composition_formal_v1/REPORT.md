# Useful-control provenance composition formal v1 — first outcome

Disposition: `PASS_USEFUL_CONTROL_PROVENANCE_COMPOSITION_SCOPED`.

Exact merged #963 composition Git blob `b78ced2ca877b7c8ba28ec093c531ad4d2cbb73a` and #941 parent interval-contract blob `979f257b4f02be80bcaa30ae8d5a0aa92162bfb1` were held fixed.

One source-first formal invocation, reruns/replacements/tuning 0:
- fresh valid/mixed seed `96320260917011`: **100,000/100,000** exact equality against a separately authored discrete-set oracle for all four aggregate occupancy bounds, every per-actuation bound, and all six effect buckets;
- fresh adversarial seed `96320260917012`: **50,000/50,000** exact gate/bucket precedence matches, comprising 20,000 Gate1/Gate2 fail-closed exception cases and 30,000 record-role/precedence cases;
- fixed boundary controls: **11/11 PASS** including exact-at-down, post-release, negative-before-unscored, positive-pre-down unscored, positive-pre-down scored, unknown lineage useful/nonuseful, malformed lineage before negative time, duplicate/invalid IDs and whitespace-only rejection;
- model/network/task-input/authority actions: 0.

Independent audit passed with `errors=[]` and no formal rerun. Five copied-result corruption mutations were all rejected: valid count, adversarial count, source hash, disposition and rerun count.

Formal diagnostic timing in the current container: runner internal loop `5.065079834 s`; outer `/usr/bin/time` wall `5.65 s`; max RSS `93,360 KB`. These are harness diagnostics, not a performance claim.

Scope remains synthetic same-process integer-time measurement semantics. This does not establish X11 physical truth, distributed exactly-once delivery, MAP01 usefulness, planner latency, token savings, human tempo or a production ABI. A later live-instrumentation rung must remain separately authorized.
