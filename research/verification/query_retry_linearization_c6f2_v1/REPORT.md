# Query/retry linearization result

## Decision

**PASS_QUERY_RETRY_LINEARIZATION_SCOPED**

Formal denominator: 54 cases. Construction: 27 separate cases, excluded.

| policy | formal cases | extra same-operation effects | changed-payload effects | final counter sum |
|---|---:|---:|---:|---:|
| CACHE_QUERY | 18 | 8 | 2 | 30 |
| SPLIT_RECHECK | 18 | 6 | 2 | 28 |
| ATOMIC_DEDUP | 18 | 0 | 0 | 20 |

The 8 and 6 totals include changed-payload effects; they are not all identical-payload duplicate executions.

## Interpretation

A correct `NOT_FOUND` result describes the instant of its read. It does not prevent the original request from committing afterward. Repeating the read in another transaction narrows the interval but does not eliminate the check/use gap.

In the directed `ORIGINAL_BETWEEN_PREPARE_COMMIT` schedule, `SPLIT_RECHECK` observed `NOT_FOUND` twice, then the original worker committed, then retry committed a second effect. The individual read results were not false.

`ATOMIC_DEDUP` instead rechecked exact operation identity/content inside the same `BEGIN IMMEDIATE` transaction that could apply the effect. When the original had already committed it returned the existing result; if the payload differed it returned conflict; if the retry won the race, the later original saw the retained operation and did not apply another effect.

This is an application transaction contract. It is not a generic GUI exactly-once solution.

## Retention boundary

The intake-main `runtime/cli_v1/attempt.py` blob was copied byte-identically and used for 84 retained commit-attempt invocations. Each actor used a distinct run directory. Retention records remained `replay_allowed=false` and `process_state=unknown`; `report_recorded` was not treated as generic task success.

The module does not promise deduplication across run directories; this experiment therefore does not identify a defect in that module.

## Audit

- 54/54 formal cases
- 108/108 worker exits
- 2/2 outer batch exits = 0
- raw-only audit errors = []
- 12/12 evidence corruptions rejected
- source freeze verified after execution
- no formal rerun/replacement/pooling/tuning

Corruptions include dropped/duplicate case, altered effect, valid-JSON authority grant, bool-as-int identity, missing exit, altered report, query reading effect table, and removal of the candidate transaction boundary.

## Scope

Provided Linux x86_64 execution container, Python 3.13.5, SQLite 3.46.1, DELETE journal, synchronous FULL. No Docker/OrbStack image attestation. No model, GUI/input, external network experiment, credentials or user data.

Three finite repetitions? No: exactly two formal repetitions per policy/schedule. These are directed counterexamples, not a reliability-rate estimate. Diagnostic clocks are not benchmark evidence.

## Integration handoff

For #2789 recovery semantics:
- a negative status is evidence, not retry authority;
- a later separate status read still is not a reservation;
- promotion to a real side-effect path needs semantic operation identity enforced at the effect boundary, or an application-specific equivalent;
- when the effect cannot share the transaction, keep outcome uncertainty explicit rather than assuming safe replay.

Parent #24 and broader #2084/#2789 questions remain broader than this result.
