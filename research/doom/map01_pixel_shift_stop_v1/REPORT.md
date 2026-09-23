# MAP01 pixel-registration stop — formal result

Task `MAP01-PIXEL-SHIFT-STOP-20260917-002`, Issue #719.

## Decision

**`PASS_PIXEL_SHIFT_STOP_SCOPED`**.

A1 (`...-001`) is retained separately as `STOPPED_SETUP_OUTPUT_PRECREATED`: the formal runner was invoked once but failed before the first case because the outer wrapper pre-created its exclusive output directory. A1 contributes zero rows. A2 changed only identity/output supervision; frozen science source, metric, 34 px gate, seeds, arms and evaluator gates were unchanged.

A2 produced 16/16 first outcomes in one runner invocation, no retry/replacement/tuning. Frozen audit passes with zero errors.

## Main matched cases

| seed | perturb pulses | shift correction pulses | shift terminal yaw error ° | MAE correction pulses | MAE terminal yaw error ° |
|---:|---:|---:|---:|---:|---:|
| 996101 | 1 | 0 | -5.273437 | 1 | 0.000000 |
| 996101 | 3 | 3 | -1.757812 | 3 | 0.000000 |
| 996101 | 6 | 5 | -5.273437 | 6 | -1.757812 |
| 996102 | 1 | 0 | -5.273437 | 1 | 0.000000 |
| 996102 | 3 | 2 | -5.273437 | 3 | 0.000000 |
| 996102 | 6 | 5 | -5.273437 | 6 | -1.757812 |

- `HORIZONTAL_SHIFT_STOP`: 6/6 main cases finish within the independent ±6° yaw gate; false MATCHED 0/6.
- `RGB_MAE_STOP`: 6/6 also finish within ±6° on these fresh held-out seeds, but two 6-pulse cases exhaust the full correction budget despite ending near reference.
- Candidate is non-worse on task correctness in 6/6 pairs and uses fewer correction pulses in 5/6 pairs. Lower-displacement candidate cases all use <6 correction pulses.
- Both aligned controls stop with zero correction input. Both missing-reference controls return `UNKNOWN_MISSING_REFERENCE` with zero correction input.
- All cases finish with neutral key state, verified owner release where input occurred, and zero deaths.

The result therefore supports a scoped **termination-relation improvement**, not a broad image-registration or angular-control claim. The fresh A2 comparator happened to remain task-correct in all six main cases; the benefit here is avoiding unnecessary continuation while preserving correctness. The predecessor #710 negative remains canonical evidence that raw RGB MAE can reject a task-valid near-reference view and continue away.

## Integrity

Formal summary SHA-256 `db4c2e40ec4f4c830dd61cba0f91715dcdfc5f58f0a92349bee74eae666135fd`; compressed exact summary SHA-256 `819f1a3403615f72c7bf457b6db8df9880799dfe393eb4ceed345ce67c295995`. Frozen audit has zero errors, postformal frozen-source rehash passes, frozen tests re-pass 4/4, and eight direct copied-evidence mutations are rejected 8/8. The GitHub-retained compact evidence archive contains the exact formal summary, audit, source-rehash receipt, mutation controls, A1 stop receipt, A2 plan/freeze and supervision logs; its SHA-256 is `23e40db79137629c873b758e66ef97fc6b136a913243e52438d38020090e9b96`. The exact formal summary retains each reference/current PNG SHA-256. A full 67-PNG byte/size manifest and the PNG bytes are retained in the conversation-side full evidence archive; GitHub publication does not claim those PNG bytes are present.

## Boundary

Yawed perspective views are not pure translations. NCC correlation magnitude is not a success gate; the hard false-stop check remains independent evaluator yaw. The 34 px mapping is geometry-derived for this 640 px / 90° view and is only locally supported at the fixed MAP01 start. No general target identity, navigation, threat/survival, model/token, MAP01-clear, cross-scene reliability or production-runtime promotion follows.
