# Win32 live fixture recovery experiment r02

Date: 2026-11-10 (Asia/Tokyo)
Target: repository-owned `Agent Interface Win32 Fixture`.

## Question and setup

This run attempted to observe a public supervised-Win32 pending dispatch and its terminal result, while preserving the process custody and testing recovery if the public result could not be obtained. The run used one fixture and one `A` input. Raw requests, responses, event files, producer records, recovery receipts, and cleanup records are retained in this directory.

## Outcome

The dispatch returned `pending`. The probe incorrectly interpreted a missing top-level `status` field in an `interface_results` response as a non-pending terminal result, then attempted close while the action was still running. Close returned `busy` and did not invoke an operation. This is a probe/parser failure; it is not evidence that the public operation completed or that ordinary completion cleanup failed.

The durable producer record later showed completion and a verified release receipt. A separate exact-source recovery call then returned `recovered`, confirmed neutral native readback, and verified a 2,000 ms late-input observation horizon (76 samples; maximum sample gap 32 ms against 100 ms allowed). Persistent custody is clear for that source operation/generation. The source action remains `UNKNOWN`, `task_success` is null, and replay is denied. The fixture was closed and exited.

## Interpretation and limits

This packet preserves a failed observation harness together with successful bounded cleanup/recovery evidence. It does **not** establish a normal-completion horizon through the original public caller, a task-success oracle, MAP01/GZDoom control, hard physical-release deadline, continuous neutrality between samples, broad reliability, or efficiency. Do not count this run as the normal-completion pass; see r03 for that separate discriminator.

## Evidence

`conditions.json`, raw MCP dispatch/results, event captures, durable producer receipt, exact-source custody snapshot, recovery request/result/log, probe source and log, and cleanup are retained. `SHA256SUMS` covers all packet files except itself.
