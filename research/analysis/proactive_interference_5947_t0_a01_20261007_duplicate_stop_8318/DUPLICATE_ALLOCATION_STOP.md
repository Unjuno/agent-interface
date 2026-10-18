# Duplicate-allocation STOP

**Disposition: `STOP_DUPLICATE_ALLOCATION_ALREADY_CONSUMED`.**

The formal candidate and auditor invocations recorded in `RUN_RECORD.json` did occur once each and their raw outputs remain byte-preserved in `results/`. Subsequent GitHub inventory found predecessor PR [#8317](https://github.com/Unjuno/agent-interface/pull/8317), which already used allocation `5947-MULTI-UPDATE-PROVENANCE-T0-A01-20261007` on base `798ac5ad709168ff1d27b115f10f4f96b126bb71` for the same fixture-only T0. The predecessor records `HOLD_AUDITOR_COVERAGE` because its audit did not establish complete baseline-record equality/source identity and exact serialized bytes outside the history slot.

Therefore this later execution is an accidental duplicate, not an authorized successor or independent allocation. Its apparent process-level auditor PASS is retained only as custody evidence; it does not change the predecessor HOLD and cannot repair, replace, pool with, or supersede that result. No candidate/auditor rerun was made after discovering the conflict. Any future work requires a genuinely distinct, separately reviewed question/allocation and must preserve both prior records unchanged.
