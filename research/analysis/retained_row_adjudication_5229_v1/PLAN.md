# #5229 retained-row adjudication, explicit assumption comparison

Worker 01a0ff35-2ef3-7911-9911-f31862ad642f; FINAL-v5; host CPU/stdlib only.
Source intake f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549. Ordinary analytical
evidence validation, not a new kernel experiment or formal allocation.

- H: the reported five raw-case disagreements depend on release/end and effect
  equality meanings that the retained record does not independently establish.
  Original scientific gate remains unevaluable under every listed interpretation.
- T: pin the exact #5216 raw, probe, PLAN, legacy audit and manifest; read them
  without executing/importing historical code. Compare all nine observed booleans
  under three release meanings and two effect-equality meanings. A separate
  implementation checks the source's AST literals and the complete six-way
  arithmetic table, with missing/type/duplicate and actual corruption controls.
- D: PASS_ADJUDICATION_SCOPED requires exact source/raw pins, complete six-way
  enumeration, matching independent audit and refusal controls. Each original
  gate is HOLD_UNEVALUABLE if effect-at-900 is absent or the two original equality
  statements conflict. No conditional mismatch is a new observed runtime outcome.
- C: snapshot-only checks release identity/emptiness without a time relation;
  post-execution means release at/after execution end; terminal-includes-release
  means release lies within execution start/end. Compare effect-at-end admission
  under >= end and > end. None of these candidates is adopted as the old contract.
- U: frozen authored source parameters plus nine stored booleans, not actual
  temporal logs. Same-clock interpretation is stipulated, not measured. Context
  inconsistent under an interpretation gives UNKNOWN_CONTEXT for dependent
  effect rows; do not turn those unknown rows into negative observations.

## Variable definitions and units

| Field | Japanese meaning / definition | SI unit | Assumption / range | Type |
| --- | --- | --- | --- | --- |
| lease_end_ns | 権限leaseの排他的期限 | s; stored in ns = 10^-9 s | 1000; common clock stipulated | nonnegative integer scalar |
| begin_ns | 固定ソースで実行開始要求を受理する時刻 | s; stored in ns | 300; no measured latency | nonnegative integer scalar |
| start_ns | receiptが宣言する実行開始時刻 | s; stored in ns | 500; same clock stipulated | nonnegative integer scalar |
| end_ns | receiptが宣言する実行終了時刻 | s; stored in ns | 700/999/1000/1001; end role compared | nonnegative integer scalar |
| release_ns | 空入力snapshotの観測時刻 | s; stored in ns | 800; relation to end is not stipulated by raw | nonnegative integer scalar |
| effect_ns | 効果snapshotの観測時刻 | s; stored in ns | 499/699/700/701; 900 is absent | nonnegative integer scalar |
| accepted | 保存済みprobeの受理/拒否値 | 1 (dimensionless) | raw observed values only | exact boolean scalar |

Comparisons use integer order on one stipulated clock, so no mixed-unit
arithmetic or timing estimate is made. No kernel/probe/audit/generation code
from the historical package is executed. No container/model/GPU/GUI is used.
