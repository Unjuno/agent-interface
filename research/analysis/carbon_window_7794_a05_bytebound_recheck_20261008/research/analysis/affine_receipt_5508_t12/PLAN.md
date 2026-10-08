# Issue #5508 T12 — cross-store crash recovery with semantic observation

## H/T/D/C/U

- **H:** With receipt consumption persisted in one SQLite database and the simulated external effect persisted independently in a second, recovery after a real child-process kill will report `CONFIRMED_SAME_ATTEMPT` only when receipt attempt/delivery identity matches the external delivery and an independent observer sees the declared semantic postcondition. Missing, mismatched, or unavailable evidence remains `UNKNOWN`; a crash before consumption remains `NOT_STARTED`.
- **T:** One deterministic run of seven hand-authored crash/recovery traces in a network-disabled Python 3.12 container: kill before receipt consume; kill after consume/before effect; kill after external effect commit/before observation; matching lineage but wrong target; mismatched attempt/delivery with a target-looking external state; matching effect with observer unavailable; and a normal valid completion. Receipt journal and external-effect store are separate file-backed SQLite databases. Two recovery cases re-present the consumed receipt and require rejection without a second external delivery. The observer runs as a separate process. No RNG, GUI, model, MAP01, external network, or tuning.
- **D:** `PASS` only if all seven frozen outcomes match: one `NOT_STARTED`, four or more conservative `UNKNOWN` states as specified in the trace table, and exactly two semantic confirmations (one recovered after kill, one normal); no case confirms unless the consumed receipt's attempt and delivery match the external effect and the observer's target equals the intended target; every consumed receipt admits at most once; the two replay attempts are rejected and effect delivery count remains one. Any false confirmation, duplicate admission, lost exact-effect confirmation, or outcome mismatch is `FAIL`.
- **C:** A receiver with a truly atomic transaction spanning receipt and effect, or a durable idempotency service that also preserves attempt identity, may make this journal unnecessary. `UNKNOWN` after receipt consumption but before an observable effect is an intentional safety/liveness tradeoff.
- **U:** `SIGKILL` tests process death, not host power loss, storage corruption, networked databases, or arbitrary GUI effects. The external effect and semantic observer are local authored simulators; their truthfulness and filesystem durability are assumptions. This is not a production or distributed-systems guarantee.

## Frozen seven-case matrix

| Case | Crash/effect condition | Required recovery result |
|---|---|---|
| `pre_consume` | SIGKILL before atomic consume; no effect | `NOT_STARTED` |
| `post_consume` | SIGKILL after consume commit; no effect; retry same receipt | `UNKNOWN`; retry rejected |
| `effect_pre_observation` | exact external effect committed; SIGKILL before caller observes; retry same receipt | `CONFIRMED_SAME_ATTEMPT`; retry rejected; one effect |
| `wrong_target` | matching attempt/delivery, observed target differs | `UNKNOWN` |
| `foreign_lineage` | target-looking effect exists under different attempt/delivery | `UNKNOWN` |
| `observer_unavailable` | matching external effect; observer unavailable | `UNKNOWN` |
| `normal_valid` | normal consume, external effect, and observation | `CONFIRMED_SAME_ATTEMPT` |

The candidate runner was invoked once during construction before source hashes were frozen or a GitHub preregistration comment was posted. It unexpectedly executed the entire seven-case matrix while only a smoke check was intended. Therefore this is an **exploratory construction pilot**, not a preregistered/confirmatory result. The stdout was captured in the tool execution output and transcribed into `raw/construction-pilot.jsonl` after the command; stdout was not redirected to a file during the run. The SQLite state files were copied from that exact run. Do not rerun this matrix. A distinct, disjoint successor allocation requires its own source freeze and preregistration.

The captured stdout is retained as `raw/construction-pilot.jsonl`; file-backed SQLite databases were copied from that exact invocation into `raw/db/`. A separately authored auditor reopens those databases and reconstructs expected states. Corruption controls must reject missing-case, altered-lineage, forged-confirmation, and duplicate-delivery artifacts.

## Lineage

Issue #5508 T0–T11 remain immutable. T12 specifically moves beyond data-only crash-boundary models by killing OS child processes between commits to two separate durable local stores. It does not repeat the earlier 20-connection uniqueness stress as its primary gate.
