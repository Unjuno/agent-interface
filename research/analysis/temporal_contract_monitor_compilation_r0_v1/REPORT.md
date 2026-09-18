# #1719 First formal stop: same-timestamp predicate-transition oracle defect

Raw decision: **FAIL_TEMPORAL_MONITOR_SEMANTICS**

Postformal scientific disposition: **FAIL_INTEGRITY_ORACLE_SAME_TIMESTAMP_P_TRANSITION**. The semantic theorem is **not decided** by this allocation.

## First/only formal outcome

- formal invocations: **1**
- reruns/replacements/tuning: **0/0/0**
- traces: **1,062,624**
- prefix checks: **5,144,928**
- candidate/oracle mismatches: **168**
- independent audit recomputed mismatches: **168**
- reachable-outcome checks: pass
- malformed descending-time controls: pass
- P-false-reset corruption control: **failed**

All mismatches are in `P_CONTINUOUS_FOR` for tau=2 or3.

Representative retained counterexample:

`(0,true) -> (1,false) -> (1,true) -> (2,false)`, tau=2.

The candidate remains PENDING because the explicit false fragment at t=1 breaks continuity and the new true run starts at t=1. The reference oracle groups all same-timestamp predicate fragments and retains only the final value at t=1, erasing the false reset. It therefore incorrectly carries the earlier t=0 true interval through t=1 and reports SATISFIED at t=2.

The independent auditor shared the same last-value coalescing rule, so its agreement does not rescue the result; this is a correlated oracle defect.

## Preserved facts

The event-set contracts AB/CD/XY had no candidate/oracle mismatch in this first allocation. This is diagnostic only, not a separable PASS, because the frozen formal decision covers the composed four-family contract.

The candidate's fail-closed descending-time behavior and fixed-size state shape also passed, but are not promoted independently.

## Integrity

The source was frozen and GitHub-readback matched before formal. Exact result/audit bytes are retained in deterministic gzip+base64 form. The first allocation is consumed and will not be rerun.

A legitimate successor changes exactly one factor: the P reference semantics must preserve every same-timestamp Boolean transition in arrival order while still treating zero elapsed duration correctly. Candidate monitor and AB/CD/XY semantics should remain unchanged.

No model, GUI, X11, network, task input or shared runtime was used.
