# Issue #3808 formal-01 result

## Decision

`PASS_CALLER_RECOVERS_AFTER_DOWNSTREAM_TRUNCATION_SCOPED` — one OrbStack/Linux/arm64 formal runner invocation produced four rows. A separate fresh container independently audited the retained raw bundle and returned `PASS_AUDIT_CALLER_RECOVERY_SCOPED`, `errors=[]`.

The producer path ran the current CLI `main()` with only the dispatch facade replaced by a deterministic completed synthetic receipt. Its relay accepted all serialized response characters and returned the full write count to the CLI. The delivery side then exposed only the frozen 37-byte prefix to the caller. The producer exited 0, while the caller could not parse the prefix. The caller used the real `attempt-status` command, then the real read-only `review` command against the same run directory. It recovered the completed outcome from `report.json`; the dispatch facade was called exactly once and the attempt-directory hashes were unchanged across recovery.

| Case | Producer/status exit | Dispatch count | Observed result |
|---|---:|---:|---|
| Complete-delivery control | 0 | 1 | Full response parsed as completed |
| Downstream strict-prefix delivery | producer 0; status 0; review 0 | 1 | 341 accepted bytes; caller received 37 bytes and could not parse them; retained report recovered as completed |
| Request-only control | status 2 | 0 | `unknown_or_incomplete`, `replay_allowed=false` |
| Existing destination control | 2 | 0 | `REQUEST_PERSISTENCE_FAILED`; existing sentinel preserved |

Formal raw SHA-256: `07b761e6c9c4f03c5cce3fdc2f64bdc7017da3d97e6f30a9ac312a3b418b902f`

Independent audit SHA-256: `799cd2f12527f53334a266f8070138893981a37bc8ab99e3e420ef9dfb843983`

Raw evidence: [`results/formal-01/raw.json`](results/formal-01/raw.json)

Independent audit: [`results/formal-01/audit.json`](results/formal-01/audit.json)

Frozen allocation and container commands: [`PLAN.md`](PLAN.md), [`CONTAINER_RUN.md`](CONTAINER_RUN.md)

## Scope and limitations

This is a synthetic-only deterministic test of the public CLI entry point, its retained attempt/status/review paths, and a simulated intermediate relay truncation. It establishes that exit 0 after full producer-side acceptance does not prove downstream receipt, and that this caller can recover a retained completed report without redispatch in the tested case. It is not an actual network/OS pipe truncation, GUI or user task, model-visible delivery, power-loss guarantee, latency/token benefit, or general caller reliability result. The read-only `review` output had no image to show; the audited success was the retained synthetic completed outcome. Issue #3711 remains open for broader adoption and live-use gates.
