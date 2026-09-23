# Mixed known/unknown composed X11 gate audit

## H/T/D/C/U

- H: a composed gate routes known frames to the local classifier, rejects unknown fresh frames at OOD, and accepts only positive target predictions above confidence 0.75.
- T: mixed block: base 160, old shift 160, fresh 160. OOD uses the fixed base 99th-percentile distance threshold; classifier trains on base 160 + old shift adaptation 80. Formal accept = OOD pass + predicted target + confidence >=0.75.
- D: source-bound X11 raw frames/manifests and CUDA RTX 3080.
- C: fixture-only composition result; no semantic/runtime/token/latency/gameplay claim.
- U: fresh must be OOD-YIELD with zero classifier calls; accepted false positives are FAIL.

## Corrected result

| set | OOD YIELD | classifier calls | target accept | accepted false |
|---|---:|---:|---:|---:|
| base | 0 | 160 | 21 | 0 |
| old shift | 17 | 143 | 9 | 0 |
| fresh | 160 | 0 | 0 | 0 |

The first mixed aggregation incorrectly counted high-confidence negative predictions as accept and was discarded. The corrected target-class condition above is the formal result. No runtime promotion.
