# Two-displacement X11 reversal observability ceiling A2

Issue: #1354  
Task: `TEMPORAL-X11-DISPLACEMENT-OBSERVABILITY-CEILING-A2-20260918-014`

Formal discipline: source-first publication/readback, ownership reread, exactly one formal runner invocation, reruns0. Corruption controls5/5 rejected; source rehash exactly matches the preformal freeze.

## Retained first outputs

Frozen auditor output: **`HOLD_BLIND_TAIL_NOT_SUFFICIENT`**, errors[].

The frozen auditor has a retained decision-wiring defect: when every required witness/count/ceiling check equals the preregistered value, its `science[]` remains empty, and the final branch incorrectly maps empty science to HOLD. The formal result is not rerun or modified.

Applying Issue #1354's already-frozen D criteria read-only gives scientific classification: **`PASS_TWO_DISPLACEMENT_OBSERVABILITY_CEILING_A2_SCOPED`**.

- All published #1344 boundary displacement patterns are full-motion compatible under nominal7.3px ±0.75px.
- age100: 12/12 UNKNOWN rows have phase>0 blind-tail opposite-current witnesses; safe ceiling remains 188/200 = **0.94**.
- age200: 12/14 UNKNOWN rows have phase>0 blind-tail witnesses; only the two phase0 rows are timing-identifiable; safe ceiling becomes188/200 = **0.94**.
- Both ceilings stay below #1344's frozen0.95 recovery gate.
- Witness construction: for phase>0, place one reversal halfway between the newest sample and query. It changes current direction while leaving every sampled displacement unchanged.

Therefore this two-displacement representation cannot safely reach the frozen recovery target merely by tightening the already validated displacement bound. Additional current evidence or a stronger motion assumption is required.

This is a contract-level observability statement. It does not claim that full raw images are identical, and it is not live X11/model/task evidence.

Artifact SHA-256:
- FORMAL_RESULT `25acf798f1d698a85e62391969e4f415008ffd916fd290a729772ff751d2743e`
- frozen AUDIT `d6ec4cccb5667d9e5f6ed02eb7344db1b94ff9c9c2cfe4cc7c25c8b06056cb1b`
- CORRUPTION `fee3976ced4021c1799523eb145aeebb82d06d177bdf6e90a16e601f32008dbe`
- POSTFORMAL_CLASSIFICATION `d9dc0bd97efd199c7290b16f6424fce359d8adf52f5e744e0884fbf8567e801a`
