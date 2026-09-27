# Read-receipt bypass boundary — retained result

Task `COORD-READ-RECEIPT-BYPASS-20260916-019`, Issue #508. Publication base `d95d90899686c99061f14bdd259797c0b3984f13`; source-first freeze head `8bb3c377f92c781de2b35e2091b8d30d1b688887`.

## Decision

**`RETAIN_READ_RECEIPT_BYPASS_BOUNDARY_SCOPED`.**

The effect owner still checks every token revision and commits generation in one SQLite `BEGIN IMMEDIATE` transaction. The only changed factor is read-access discipline. `tracked` routes task-relevant A and B through the receipt-producing accessor. `bypass` routes A through the accessor but reads task-relevant B through a direct SQLite query, so B participates in the decision but not in the dependency token.

| mode | scenario | token | generation commit | ground truth |
|---|---|---|---|---|
| tracked | stable | A,B | yes | correct |
| tracked | B changes rev1→rev2 | A,B | no | correct |
| bypass | stable | A | yes | correct |
| bypass | B changes rev1→rev2 | A | **yes** | **unsafe stale commit** |

In both B-change rows the decision was computed from `a1|b1`, then B durably became `b2` revision2 before effect-owner commit. The tracked token carries B revision1, detects the mismatch, and leaves generation1 with zero generation event. The bypass token carries only A revision1, sees no mismatch, and commits generation2 plus a generation event despite the task-relevant B change. The bypass B-change row is therefore `truthful=false` by the frozen oracle.

Frozen independent audit returns `RETAIN_READ_RECEIPT_BYPASS_BOUNDARY_SCOPED`, errors 0, with `unsafe_bypass_stale_commit=true`. Four copied-evidence corruption controls reject 4/4: truthful-label flip, injected B receipt, deleted generation event, duplicate measured case id. Formal measured-ID reruns: 0.

## Interpretation

Observed read receipts are sound only under a complete access discipline. A best-effort tracker cannot infer dependencies that task code reads through an uninstrumented path. Therefore the useful abstraction is not merely “record reads”; it is **mediate every effect-relevant read through a dependency-bearing capability, or require an independently bound dependency manifest at the effect owner**.

This is the direct counterexample to over-generalizing #501. #501 showed that observed receipts can reduce false contention when coverage is complete; this result shows an uncovered relevant read turns the same narrow token into an unsafe authorization.

## Retention

Full deterministic evidence archive `read_receipt_bypass_v1_evidence.tar.xz`: 5,708 bytes, SHA-256 `e9b25c9527be2101ba8fe780847e06690ad24264dfd650473864453d188a3353`; internal manifest SHA-256 `7af09a6baadfb84432b26e4ae9ca16406bd3f50ac9e2aa25fb1fb91360500efb`. GitHub retains exact frozen source, formal result/audit, corruption controls, and the archive as Base64 plus a SHA-verifying reconstruction script.

## Limits / next question

Cooperative local SQLite and one authored bypass only. No arbitrary-language instrumentation enforcement, capability sandbox, DB privilege separation, distributed concurrency, crash/power-loss or security claim. The next one-variable rung should enforce read mediation: compare unrestricted direct DB access with a capability interface where task code cannot obtain the underlying connection, and verify that the B dependency can no longer be omitted without an explicit contract violation.
