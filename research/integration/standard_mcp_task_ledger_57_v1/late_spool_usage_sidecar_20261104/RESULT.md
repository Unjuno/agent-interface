# File-spool late-usage sidecar integration check — 2026-11-04

## Change under test

The host worker now captures a same-turn late-usage cursor when its bounded App Server turn wait raises `TimeoutError`. It leaves the turn uninterrupted, publishes the immutable `unknown` receipt first, waits for at most five seconds for fresh same-turn `thread/tokenUsage/updated` notifications, and writes each matching raw JSONL row to an immutable, sequence-numbered sidecar with thread/turn identity and SHA-256. `turn/completed` is not consumed or returned; no retry or tool submission is introduced. The client closes after the grace window, including when receipt publication or harvesting fails.

## Verification

Python 3.11 on Windows:

| Run | Result |
|---|---:|
| worker, spool, App Server client, and provider adapter suite, normal | 26/26 PASS |
| existing late file-spool completion/Fake X composition, normal | 1/1 PASS |
| same module suite under `-O` | 26/26 PASS |
| same composition under `-O` | 1/1 PASS |
| `py_compile` on changed Python files | PASS |
| `git diff --check` | PASS |

The focused worker test delivers two synthetic cumulative late same-turn usage rows after observing the UNKNOWN receipt on disk. It places a matching `turn/completed` answer before those usage rows and verifies that the answer does not enter the terminal response or sidecars, both exact usage JSONL rows are hash-bound and sidecars reject overwrite, the client closes, and the claimed request is not requeued. A second synthetic composition passes a file-spool UNKNOWN plus sidecar through `FileSpoolPlanner`, `AppServerPublicMcpModelCall`, `RecordedPublicMcpCaller.observe_late_usage`, and the provider-attempt recorder after a task-score receipt. It verifies the matching protocol row, retained usage, one timeout attempt, and no Relay request.

## Limits

This is deterministic local composition evidence only. It does not prove that a real provider emits usage after a timeout, explain provider billing/cumulative semantics, automatically invoke the explicit post-score observer in every runner, or validate live GUI/task effects, WSLc, MAP01, or integrated efficiency. The UNKNOWN response remains immutable; late usage is a separate retained artifact and does not change answer eligibility or task outcome.

Raw test output and exact commands are retained in this directory. `SHA256SUMS.json` covers the packet files.
