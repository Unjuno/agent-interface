# R4 result — Issue #3885

**Decision: `PASS_MAP01_MATCHED_CAUSAL_TASK_EFFECT_CONTRACT_SCOPED`.**

The independent successor formal ran once in the pinned OrbStack linux/arm64
container with network disabled and a read-only root. It exhaustively evaluated
15 Boolean evidence gates and two event polarities: 65,536 unique rows. The
candidate/oracle mismatch count was 0; only the fully matched useful and harmful
cases were classified causal (one each); the other 65,534 rows were
`UNRESOLVED`. No row granted authority. A separate auditor re-derived all rows
without importing the candidate, oracle, or formal runner and passed 30
single-gate corruptions plus three additional laundering controls.

The predecessor #1873 source bundle is not repaired or promoted. Its committed
5,424-byte bundle disagrees with its manifest (which declares 3,680 bytes), and
the five embedded source sizes/hashes also disagree; the predecessor restore
script refuses extraction. R4 is a fresh implementation from the declared Issue
contract. Its PASS validates only this finite deterministic-fixture evidence
contract. It does not establish that ordinary stochastic MAP01 runs are
replayable, that task-effect events are a complete utility measure, or that
recovery helps in live play. No model, game, GUI, X11, ViZDoom, or task input was
used.

Formal raw data and execution record are in `results/formal-01/`. The complete
truth table is 38,207,550 bytes (65,536 JSONL rows), SHA-256
`ff2722abf17362a42c191f4c19f00a99cca1ef15d40e1b2a72d791ea68a38c03`.
