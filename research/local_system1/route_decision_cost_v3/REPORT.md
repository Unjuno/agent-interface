# Real typed route-decision cost with charged state extraction — retained result

Task `LOCAL-SYSTEM1-ROUTE-DECISION-COST-20260917-003`, Issue #900. A1 #892 and A2 #896 are retained procedural/harness stops and are not pooled. A3 is the first persisted scientific timing outcome.

## Decision

**`PASS_REAL_TYPED_DECISION_COST_SCOPED`**.

A concrete retained-style route-admission receipt was parsed and validated into an 8-bit typed state, then evaluated by exact RULE, multinomial LINEAR, and TREE backends. All three were exact on every measured query; no network, gradient, task-input or authority-grant path existed.

## Formal first outcome

- one formal invocation; reruns/replacements/tuning: **0**
- 8,192 fresh serialized nested receipts
- 32,768 measured batch-1 calls per backend phase, warmup 512
- RULE end-to-end p95: **6.990 us**
- extraction+validation p95: **5.979 us** = **85.5%** of RULE p95
- LINEAR end-to-end p95: **61.149 us** = **8.75x** RULE
- TREE end-to-end p95: **69.018 us** = **9.87x** RULE
- all backend end-to-end p95 values are <1 ms
- output correctness errors: **0** for backend-only and end-to-end paths
- setup: LINEAR 3.495 ms; TREE 0.776 ms; depth 8; leaves 11
- peak RSS: 171536384 bytes

The scoped bottleneck for the exact rule path is therefore not the branch logic itself: JSON/state extraction and evidence validation consume most of the measured p95. Generic sklearn per-call wrappers remain far below a frontier boundary but cost roughly an order of magnitude more than the exact hand-coded rule for this tiny decision surface.

## Integrity

Frozen audit: **PASS**, errors `[]`. Postformal source rehash: **6/6 exact**. Four copied-result corruptions (correctness, side-effect count, decision label, linear timing ratio) are rejected **4/4**. Formal result SHA-256 `276dd828230f5bff618c7b832ac50739e2875e711563ed8401108044f7f720f6`.

## Retained predecessor stops

- #892: `STOPPED_FORMAL_HARNESS_SEED_RANGE` before corpus/timing; no result.
- #896: `STOPPED_FORMAL_RESULT_SERIALIZATION` after timing but before persistence; no timing/result bytes reconstructed or reused.
- #900 A3 changes only the retained setup repairs required to execute/persist the unchanged science contract.

## Limits

One authored exact route-admission decision under Python 3.13 / NumPy / scikit-learn on one CPU. This does not establish learned-policy usefulness, screenshot/perception extraction cost, model fidelity, general intelligence, end-to-end computer-use latency, or a production ABI. LINEAR/TREE are compiled exact representations of a known 256-state truth table, not generalization experiments.
