# #1743 A2 formal stop: parent prefix-count gate was failure-truncated

Raw decision: **FAIL_TEMPORAL_MONITOR_SEMANTICS_A2**

Postformal disposition: **FAIL_INTEGRITY_PARENT_PREFIX_ACCOUNTING**. The semantic mismatch question is favorable but not promoted to PASS from this consumed allocation.

## First/only A2 result

- formal1 / reruns0 / replacements0 / tuning0
- traces: **1,062,624** — exact parent trace count
- candidate/reference mismatches: **0**
- independent recomputed mismatches: **0**
- retained #1719 counterexample: candidate=PENDING, primary oracle=PENDING, independent oracle=PENDING
- corruption controls: **6/6**
- reachable outcome / malformed UNKNOWN / fixed state-shape gates: pass
- observed complete prefix checks: **5,144,980**

The only failed gate was equality to parent #1719 recorded prefix count **5,144,928**.

## Why the parent number is not a valid corpus invariant

Both #1719 formal and audit stop checking the rest of a trace immediately after the first mismatch. Because #1719 had 168 mismatch traces, some later prefixes were never counted. A2 removes those mismatches, so the same generated traces run to completion and expose 52 additional prefixes.

Independent combinatorial accounting from the frozen generator gives:
- each event-label family/parameter: 149,445 traces / 724,021 full prefix checks;
- each P parameter: 5,503 traces / 25,611 full prefix checks;
- 7 event-family parameter blocks + 3 P blocks =
  **1,062,624 traces / 5,144,980 full prefix checks**.

The independent A2 audit recomputes exactly 5,144,980.

Thus A2 changed the intended P oracle factor correctly, but its D gate incorrectly treated a failure-truncated parent runtime counter as the complete corpus size.

## Integrity and next step

A2 source was frozen before the single formal invocation. Parent candidate monitor remained byte-identical. No rerun is allowed.

A legitimate A3 changes only the accounting gate:
- retain A2 candidate, primary oracle, independent oracle and generator;
- require trace count 1,062,624;
- require theoretical complete prefix count 5,144,980;
- do not require equality to #1719's truncated 5,144,928.

No GUI/X11/model/network/task-input/shared-runtime claim.
