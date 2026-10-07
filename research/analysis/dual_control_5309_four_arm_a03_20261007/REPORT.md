# Issue #5309 A03 — four-arm synthetic comparison

## Disposition

`PASS_DUAL_PURPOSE_ACTION_SCOPED` under the frozen A03 finite-simulator gate. This is a positive result for three authored action/receipt-label mappings and their explicit cost model only; it is **not** a complete validation of Issue #5309's GUI-transfer hypothesis.

## H / T / D / C / U

- **H:** A fixed dual-purpose ranker can select an already-admitted task action that advances a common subgoal and reveals the hidden target, improving synthetic completion latency while preserving the external effect-witness and release checks.
- **T:** Four arms were exhaustively run over 112 rows: 3 primary profiles × 2 hidden targets × 3 receipt conditions × 4 arms (72); a cost-reversal sensitivity profile (24); witness-loss and no-safe-path boundaries (16). One frozen candidate run and one separate frozen auditor run used host Python 3.14.5. The exact `ExecutionReceipt`/`ReleaseReceipt` dataclass source from frozen main was replayed locally; no model, backend, OS input, or authority was invoked.
- **D / result:** All 112 rows matched the independent action/effect/receipt oracle: `PASS_DUAL_PURPOSE_ACTION_SCOPED`. On the six primary fresh-receipt cases, completion was 6/6 for TASK_ONLY, EXPLICIT_SAFE_PROBE, and DUAL_PURPOSE. Mean synthetic latency was 3.0, 4.0, and 2.0 cost units respectively. TASK_ONLY had 3 wrong-target outcomes; EXPLICIT_SAFE_PROBE and DUAL_PURPOSE had 0. No synthetic collateral/unsafe effects or authority grants occurred. Stale receipts were rejected before target commits, duplicate event identities were counted once, and all 136 serialized execution receipts passed the pinned runtime contract with balanced key-down/key-up and an empty release state. DUAL yielded in both witness-loss cases; EXPLICIT_SAFE_PROBE completed both. All arms yielded in the no-safe-path cases. The cost-reversal sensitivity exposed the counterexample: explicit probing totaled 4 units versus 6 for DUAL (and 6 for TASK_ONLY).
- **C:** The latency advantage is determined by authored costs and a recovery penalty. When the probe-cost ordering reverses, explicit probing wins. Task-only recovery is an adequate baseline in this simulator. The witness-loss boundary also shows that generic information gain cannot replace an independent effect witness.
- **U:** The three primary profiles vary labels and action/receipt mappings but retain the same two-state deterministic topology; they are not a non-isomorphic or sampled held-out dynamics family. The cost units are not wall-clock measurements. Schema replay proves only dataclass compatibility, not physical release or backend behavior. No GUI, real receipt stream, live authority, model, risk calibration, task utility, or product safety is established.

## Interpretation

This result supports a narrowly specified synthetic mechanism: when a fresh decision-relevant observation is carried by a permitted progress-making action and the independent effect witness survives, information-aware ranking can reduce the frozen simulator's completion cost. It does not show that this advantage generalizes to different transition topologies. A stronger successor would vary observation/transition structure rather than only rename states/actions, and should retain the cost-reversal, stale/duplicate, witness-loss, and no-path controls. Do not pool this result with historical T0–T6 or A01/A02.

## Execution and evidence

- Frozen main: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Candidate: one invocation, exit 0, empty stderr; raw SHA-256 `dc94c4767999fe1a7ec78993bfbca6e1c16dd3f719e5dbf9fd04dfc0b464e4d7`.
- Auditor: one invocation, exit 0, empty stderr; audit SHA-256 `5951ce0e4ab58a20df5a02441385707e9b6ace71ac5670adb6c332ce1f242038`.
- Formal retries: zero. Construction defect and repair are separately preserved in `CONSTRUCTION_RECORD.md`.
- OrbStack container was not available for this run: Docker inventory failed on the pinned containerd blob with `operation not supported`. The experiment therefore ran on host stdlib Python; it did not claim OS-level network isolation.
- The source receipt contract and exact provenance are in `contracts_snapshot.py` and `SOURCE_PROVENANCE.json`. Commands and invocation counts are in `RUN_RECORD.md`; file hashes are in `SHA256SUMS.txt`.
