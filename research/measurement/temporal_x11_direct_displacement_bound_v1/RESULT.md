# Direct X11 displacement-bound transfer first outcome

Issue: #1344  
Task: `TEMPORAL-X11-DIRECT-DISPLACEMENT-BOUND-R1-20260918-011`  
Scientific decision: **HOLD_DIRECT_BOUND_RECOVERY_INSUFFICIENT**

This fresh allocation keeps the #1335 three-sample X11 sequence, localization primitive, 7.3px nominal motion, trajectory schedule, fail-closed estimator structure and recovery gates fixed. The only scientific factor is the full-motion compatibility envelope:

- baseline `POINT_COMPOSED_2PX`: +/-2.0px, obtained by composing two +/-1.0px point bounds;
- candidate `DIRECT_DISP_0P75PX`: +/-0.75px, frozen before allocation as a conservative round-up of #1326's independently measured full-step residual max0.700px.

Formal discipline: one supervisor invocation, zero reruns/replacements/tuning. 1200/1200 trajectories and3600/3600 actual XGetImage frames completed across four fresh sessions. Missed red0, point-envelope violations0, cleanup4/4.

The direct-envelope transfer gate itself passes strongly: **1506/1506 oracle-full intervals** remain within0.75px and the fresh maximum absolute full-motion residual is0.700px. Candidate wrong-direction rate is0 at every age.

| reversal age | POINT_COMPOSED_2PX | DIRECT_DISP_0P75PX | candidate UNKNOWN | candidate wrong |
|---:|---:|---:|---:|---:|
|25ms|0.15|0.19|0.81|0.00|
|50ms|0.40|0.44|0.56|0.00|
|75ms|0.65|0.69|0.31|0.00|
|100ms|0.90|0.94|0.06|0.00|
|150ms|1.00|1.00|0.00|0.00|
|200ms|0.89|0.93|0.07|0.00|

Frozen PASS required >=0.95 at100/150/200ms and >=0.05 absolute improvement over the point-composed baseline at100 or200ms. The candidate misses100/200 recovery by0.01/0.02 and improves both boundary cells by only0.04. These gates are not relaxed post hoc.

Read-only localization finds all remaining100ms UNKNOWNs at phases94..99ms and200ms UNKNOWNs at phases0..6ms. Their rasterized displacement pairs are predominantly `(7,7)` or `(-7,-7)` with a few `(8,7)` / `(-8,-7)` and `(7,8)` / `(-7,-8)`. Thus the remaining ambiguity is not caused by the0.75px envelope failing on true full intervals; mixed-motion intervals themselves rasterize to the same integer displacement pattern as full motion. Narrowing the bound below the independently validated0.75px is therefore not justified by this allocation.

## Retained audit-tooling defect

The frozen `corruption.py` raises `NameError: W is not defined` before its first mutation. It is retained unchanged and the formal allocation is not rerun. A separately labelled read-only postformal diagnosis applies the intended red-scanline, interval-truth, bound and row-count mutations to the retained raw result; the frozen auditor rejects all4 with integrity errors. This demonstrates auditor sensitivity but does not repair the frozen corruption runner or convert the HOLD to PASS.

## Scope

The sequence is geometry-equivalent to100ms sample intervals but is not wall-clock paced. The target is a trivial saturated red rectangle with known scanline. No semantic grounding, task success, model/provider, production latency or human-tempo claim follows.
