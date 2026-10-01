# Operation/target decision-row contract v1 — retained first outcome

Decision: **`PASS_OPERATION_TARGET_ROW_CONTRACT_SCOPED`**.

One source-first formal invocation, reruns0. This is synthetic contract-mechanics evidence only; **real rows counted toward #1015 remain 0**.

Formal seed `113220260918001`:
- generated single-row cases: **120,000** = 80,000 valid + 40,000 invalid;
- candidate vs independently structured oracle validity mismatches: **0**;
- invalid rows accepted: **0**;
- dataset/split cases: **20,000**;
- candidate/oracle dataset mismatches: **0**;
- split-leakage cases accepted: **0**;
- authority errors: **0**.

The retained row contract separates caller-visible `model_visible` state from independent `oracle` / post-decision evidence. Current target IDs are bound to the same observation reference and epoch. `TYPE_TEXT` may use only a caller-provided payload reference; literal generated text is not admitted. `ACTION_SET` may contain multiple independently acceptable proposals. `WATCH`, `NO_LOCAL_ACTION`, `YIELD`, and `DONE_CANDIDATE` are first-class dispositions; DONE requires an independent verifier reference. Episode IDs and split-group IDs cannot cross train/eval partitions. Model output never grants input authority.

Independent audit PASS with errors `[]`; eleven corruption controls rejected11/11. Model/GUI/task-input actions0.

Scope boundary: this result does **not** provide any real browser/desktop training or evaluation examples and does not unblock #1015 model allocation. The next rung must collect real current-state rows under this contract, with acceptable operation/target sets and explicit no-action/yield cases scored independently.
