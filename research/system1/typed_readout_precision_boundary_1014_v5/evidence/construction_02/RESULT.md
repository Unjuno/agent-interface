# Issue #4912 v5 construction result

**PASS_FP32_RECOVERS_SELECTED_CODE_TOLERANCE_SCOPED.** The one-shot construction completed 27 paired rows (9 excluded corpus pairs × FP16/BF16/FP32) on the RTX 3080. Independent raw-only audit: `AUDIT_PASS_RAW_ONLY`, 0 errors, and 5/5 corruption controls rejected. No retry; formal rows, generation, training, and optimizer steps: 0.

| Precision | Pairs within both 0.002 tolerances | Max absolute delta | Max relative delta | Peak CUDA allocation |
|---|---:|---:|---:|---:|
| FP16 | 0/9 | 0.078125 | 0.00322372662798195 | 1177708544 bytes |
| BF16 | 0/9 | 0.625 | 0.0253807106598985 | 1177905152 bytes |
| FP32 | 9/9 | 5.14984130859375E-05 | 1.93857516879066E-06 | 2359857664 bytes |

All 27 winner comparisons agreed and cache isolation passed. FP32 satisfies both gates on all nine pairs. FP16 and BF16 do not satisfy the combined tolerance gate on these rows. The result supports only the frozen selected-code construction comparison; it is not a speedup, task-quality, GUI, formal-timing, cross-device, or product claim. Invocation elapsed time of 32 seconds is retained as provenance only, not a performance claim.

The v4 pre-container STOP remains unchanged at the sibling v4 path. V5 is its fresh one-shot successor allocation; its source, command, image, corpus/model identities, and thresholds are frozen in FREEZE.json.