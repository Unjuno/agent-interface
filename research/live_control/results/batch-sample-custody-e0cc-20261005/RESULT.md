# Keep the original batch sample separate from retry samples

The current `InputOwner.release_keys_batch` takes a shared keymap sample after the ordered original UP sequence. It then reuses the same bitmap/error/time variables for each key's retry. An early key's retry therefore replaces the initial sample used to build later keys' first-attempt receipts.

This defect was reproduced against main `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`. The patch keeps `batch_bitmap`, `batch_sample_error` and `batch_sampled_ns` separate from retry-local values. Original UP order, the single shared initial query, retry bounds, and failure latches remain in the current implementation.

The new regression uses the actual raw owner thread with fake Xlib I/O and logical monotonic timestamp labels. It runs two test methods containing three cases. Before the fix (`red-v1`), the first-key retry and retry-query-error cases fail; the last-key control passes. With the same test source (`green-v1`), all three cases pass. The six existing explicit-UP/cancellation and V15/V4/V3/V13 composition tests also pass (`adjacent-v1`).

| Case | Original shared state for A / W | Before fix: W first-attempt receipt | After fix |
|---|---|---|---|
| First A UP dropped, retry succeeds | down / up | Uses later retry timestamp | Uses shared timestamp |
| Last W UP dropped, retry succeeds | up / down | Shared timestamp retained | Shared timestamp retained |
| First A UP dropped, its retry query fails | down / up | Unknown state and A's retry error; W retained as owned | W remains verified up at the shared sample and is removed from the held map |

In the last case A remains unverified, `release_pending` remains true, and a following DOWN is rejected with no new KeyPress. Verified cleanup terminates the fake owner and leaves no fake keys down. The patch therefore repairs W's evidence without treating A's unknown release as successful. All original UPs precede the post-batch sample; no keymap query is inserted between them.

All red/green traces, test stdout/stderr, command/exit receipts, source hashes, and original code are retained. `construction-note.md` records the initial export error, which occurred before any owner or test ran. Ordinary repair regressions are not consumed formal allocations.

Scope: fake-server source/receipt correctness only. Synthetic timestamp labels are not measured latency. No real X server, GUI/native input, game, model, container or physical-release/task-effect experiment ran. This repairs a prerequisite for trustworthy batch telemetry; it does not implement the complete V15/A01 adapter or establish independently useful feedback, live threat response, recovery efficacy, or MAP01 completion. Main integration remains subject to FINAL-v5 nonauthor quorum and exact-current-tree verification.

The existing nonauthor agent reviewed the exact patch and retained raw without rerunning any candidate. Final audit v2 passes. The first audit failed because its expected red-mismatch list omitted the separately visible later-key unknown-state consequence of the same sample contamination; original v1 source and FAIL output are retained alongside the corrected audit. No test, raw trace or acceptance invariant was changed for the audit. This review is not a content-quorum vote.
