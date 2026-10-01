# #1206 first outcome — retained integrity failure

Task `OPERATION-TARGET-PAYLOAD-ARGUMENT-COMPLETENESS-20260918-001`.

## Execution
Construction controls 9/9 passed before source-first freeze. Ownership reread was clean. Exactly one 96-row primary replay was then executed; reruns/replacements/tuning0. Exact #1133 corpus semantic digest was reproduced. No model, GUI, provider, network or task-input action occurred.

## Raw primary
The frozen safe rule returned an acceptable disposition on **96/96** rows: positives48/48, semantic negatives48/48, false executable negatives0, missing executable arguments0 after adding the actual caller payload_ref value.

However the primary collision counter reported4 conflicts because it intersected literal target/payload argument values across different rows. Opaque target/payload values are output arguments only and were explicitly forbidden as decision keys.

## Independent postformal contract audit
Recomputing conflict groups with target IDs alpha-renamed to candidate slots and payload values normalized to argument presence gives:
- literal conflict groups:4;
- alpha-normalized incompatible conflict groups:**0**.

Therefore the primary's recorded HOLD is not a valid representation conclusion. The allocation is retained as **FAIL_INTEGRITY_COLLISION_NORMALIZATION**. The primary is not rerun or relabelled as PASS.

Raw primary SHA-256: `c1d2c8b61db1d17ac513d93ec3e93a60af46191df496fbbc693f2cb977e3a73f`.
Integrity review SHA-256: `8d329c7d7cad0ddd19c1322a0a78894aae36cfbcc528fecf0293217bc951962d`.

## Boundary
This failure is in the analysis harness, not evidence that the representation fails. A fresh successor may change only the collision normalizer and rerun the same frozen representation/rule/corpus under a new allocation ID.
