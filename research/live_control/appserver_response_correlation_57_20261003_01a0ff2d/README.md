# App-server response correlation: first observed counterexamples

Source at cf2a0d59b5a147fb1918eb34f5bc03242336df05: `research/live_control/codex_app_server_client_v2.py`, 6508 bytes, Git blob fa0ef74a0e6202eeea1ae9760423558f4ca39b28. Prospective allocation: issue 57 comment 5969900553. This archive changes no production source or entry point.

One first matrix ran twelve owned native Windows stdio dummy-peer cells: six conditions, unchanged source versus a private one-line classification comparator. Each cell sent one request and never retried it. The peer emitted a notice and test prefix, awaited an explicit fixture gate, then sent the sole proper integer-ID response or typed error. These are synthetic protocol packets, not actual provider/model messages or complete approval payloads.

| Condition | Original | Private exact-int/no-method comparator |
| --- | --- | --- |
| healthy integer response | correct result | correct result |
| boolean `true` ID prefix | wrong prefix accepted as success | correct final result |
| floating `1.0` ID prefix | wrong prefix accepted as success | correct final result |
| string `"1"` nonmatching prefix | correct final result | correct final result |
| request-shaped `id:1` plus `method` prefix | premature KeyError instead of final response | correct final result; request packet retained |
| integer-ID typed error | typed error preserved | typed error preserved |

Python dictionary key equality makes `True` and `1.0` alias minted integer ID 1. The unchanged reader also classified any packet carrying an ID as a response, including the synthetic server request. The private comparator admits only exact Python int IDs without a method. It is diagnostic evidence, not a complete repair: it does not implement approval handling, complete response validation, active-request membership, bounded quarantine storage, or general malformed-message policy. Existing stderr-drain/constructor/EOF/journal/reader source owners remain responsible for production integration.

First driver: 2026-10-03 14:06:33.015543–14:06:36.839142 UTC, PID 32996, exit 0. RAW.json private original: 62597 bytes, SHA-256 a2615900dc8e48f0508aff1524fb66aab7b9f292ba4f9aec50fce31d9e7ac75c. Exit 0 means expected counterexamples captured; it is not a production pass.

A separate saved-data oracle joins all twelve original wire/journal/source/terminal/cleanup records. It finds three mismatches in the original and none in the six comparator cells. Six full copied corruptions were rejected: promoted wrong result, erased server request, invented resend, removed final wire record, erased typed error, and claimed an unretired reader. No driver or peer was rerun.

The first oracle failed (PID 40076, exit 1) because its strict timing inequality assumed distinct readings from the Windows monotonic clock. That failure, source, stderr and receipt are retained. V2 changes only strict inequalities to nondecreasing inequalities and uses gated wire/state causality (PID 27360, exit 0). Later clock metadata reports GetTickCount64 resolution 0.015625s for monotonic, and QueryPerformanceCounter resolution 1e-7s for perf_counter. There is no high-resolution timing, speedup, hard deadline, actual model usage, real GUI task, input-release or full goal-completion claim.

Official upstream semantic reference: [OpenAI Codex rpc.rs](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/src/rpc.rs), which separates request/notification/response/error and represents request IDs as strings or i64 integers. This does not establish the installed backend version or suggest it actually emits these synthetic malformed packets.

`evidence.json.gz.b64.txt` is base64 of a gzip JSON capsule. Decode base64, decompress gzip, parse JSON, then decode each member's content_base64. Verify all public member sizes/hashes against MANIFEST.json; retain every member as data. Python snapshots have a .py.txt suffix. Public data replaces only user-local workspace/Python paths; compressed copied controls were decompressed, path-projected and recompressed. Original private hashes and public projected hashes are separately declared. Historical hashes inside projected records refer to private originals, so do not execute the projected oracle against original freeze hashes. The private original audit result remains a scoped observed result, not a public replay claim.

The broad physical computer-control/resource-efficiency goal remains ACTIVE. Prospective evidence review and any later production delivery require their own exact content quorum and actual integration binding.
