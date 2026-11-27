# G10 unreturned-call ledger and exact server reconciliation

## Result

The ledger now snapshots each tool attempt before awaiting the MCP response. A 1 ms client read deadline on the compiled G10 call leaves an UNKNOWN row with request hash, `invocation_started=true`, no caller call ID, no caller response/report hash, and null task success. The stdio server had in fact persisted a unique compiled-call request/report before the client deadline was raised.

The finalizer can recover that server call ID only by reconstructing the caller arguments from the stored MCP request representation (`response_wait_ms` is moved back to `wait_for_result_ms`) and requiring exactly one canonical request-hash match. It stores the server call ID and raw request/report hashes in separate `server_*` fields; the caller receipt stays absent, effect remains UNKNOWN, task success remains null, and replay remains false. Zero or multiple matches are retained as no-match/ambiguous without selecting a row.

The matched report has a `TASK_SUCCEEDED` compiled-method receipt and both action releases verified, while its task-level effect is still UNKNOWN pending verified close and target exit. The independent no-timeout fixture completes normally, verifies saved effects, releases, and close.

## Verification and custody

The final source module passed 3/3 in normal and optimized Python. Raw timeout/success attempt ledgers, child request/reports, combined stdout/stderr, conditions, and a SHA-256 manifest are preserved here. Published logs redact the checkout path.

## Limits

This is Fake X/process stdio evidence. It proves a caller-side accounting/reconciliation rule for this test harness, not general production crash durability or real network partitions. Provider usage remains UNKNOWN; there is no live Calc route comparison, cold/warm/invalidation/repair economics, or MAP01 task-success result.
