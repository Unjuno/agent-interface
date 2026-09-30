# Issue #5508 T14 — concurrent sink delivery admission

## Disposition

**PASS for the preregistered two-case local sink gate.** The eight children in each case all reached READY before the shared filesystem latch was released; all 16 exited zero. The independent auditor reconstructed receipt lineage, per-child outcomes, sink rows, and target state from both retained DBs and returned PASS. Counts: `CONFIRMED_SAME_ATTEMPT=1`, `UNKNOWN=1`.

## Formal evidence

- Preregistration: Issue comment [#5912788757](https://github.com/Unjuno/agent-interface/issues/5508#issuecomment-5912788757), before formal allocation.
- Base HEAD: `ae727543f47e48bb1686e706b21ed5d9ba1cc31d`.
- Runtime: OrbStack Docker, Linux/ARM64, `--network none`; `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Frozen runner SHA-256: `5878cb372af3e127adfd2f066ca63966e0653577a0cd15382c53b8c9014cc1f0`.
- Frozen auditor SHA-256: `5ec8722b80e7dab79bbf7a83570566d03120b00d1137d97059156ddebcfbf304`.
- Frozen mutation-controls SHA-256: `f847cd88a213138815149bdd59324c0eb56e4d5d601d1890dadf298f237d4cdc`.
- Raw JSONL SHA-256: `24f5a44a4080a983907a405f0d925347eebe6740489ca92bc5c25185f05ce76b` (`raw/formal/results.jsonl`).
- Auditor: `{"audit":"PASS","decision":"PASS","errors":[],"independent_counts":{"CONFIRMED_SAME_ATTEMPT":1,"UNKNOWN":1}}`.
- Corruption controls: 3/3 rejected; output SHA-256 `1f143d757ebd574b20d7270fd5fb182a9eab1d663f312b27b7dfbf0484ccc102`.

| Case | Observed sink behavior | Recovery |
|---|---|---|
| 8 concurrent requests for `d1` | all READY before release; one insert, seven identical suppressions, one row | `CONFIRMED_SAME_ATTEMPT` |
| 8 concurrent requests for distinct `d1`–`d8` | all READY before release; eight inserts/rows, final target still `target-7` | `UNKNOWN` |

This supports the scoped rule that exact concurrent duplicate deliveries collapse to one sink row, while distinct delivery identities are not made safe merely by converging on the same final toy target. It complements T13's sequential duplicate/conflict/order cases and does not repeat the receipt-store race from T5.

## Limits

The common latch establishes that all workers were ready before release, not that their SQLite write critical sections overlapped. SQLite intentionally serializes writers on one host. No real multi-host service, network partition, power loss, cross-store transaction, API, GUI, or independently sourced semantic postcondition was exercised. The `target_state` table is an authored simulator. A PASS is limited to this local admission and audit gate.
