# Historical receipt-preservation qualification

This sidecar accompanies preservation of PR #6203 at original head `10fffc8fc1110e4f71aecb6f57b7c9ae48ae27f3`. All 20 original package files, frozen sources, outputs, plans, manifests and original dispositions remain unchanged. No parser repair or rerun was performed.

## Allocation and comparison lineage

The earlier duplicate-allocation concern was explicitly reconciled by the [owner correction](https://github.com/Unjuno/agent-interface/issues/6198#issuecomment-5938767637), which withdrew the later local execution from the evidence record and designated #6203's first preregistered run canonical. That duplicate is not an independent replicate. The original [PR hold](https://github.com/Unjuno/agent-interface/pull/6203#issuecomment-5938642937) remains part of the history, rather than being silently discarded.

The original `PASS_RAW_RECEIPT_REPRODUCED` and 12/12 retained checks are scoped to the historical parser output. The separate `PASS_PRIOR_TABLE_RECONCILED` supplement covers represented fields: 38 completed-row identities/requested durations/displayed bounds, 18 aggregate fields within 1e-9 ms, derived fractions and the interrupted-row receipt. The prior #6175 table is a posthoc transcription without completed-row keysets; direct completed-keyset comparison and authentication against missing original receipts remain unavailable. The [owner's explicit scope clarification](https://github.com/Unjuno/agent-interface/issues/6198#issuecomment-5941282509) preserves that boundary. Separate PR #6271 retains `FAIL_PRIOR_TABLE_RECONCILIATION` and interpreted HOLD; this integration does not change it.

## Omitted partial-admission start

Earlier review wording that v39 `cover-4:10` was never admitted is not supported by the [pinned raw event lines 448–452](https://github.com/Unjuno/agent-interface/blob/69a1bf509eb432e5e3c0c294d05ad7671d86adb6/research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl#L448-L452): a `Down` admission occurred before terminal cancellation, with verified-empty evidence nested in the terminal event. The historical parser/auditor consume interruption evidence from `input_released`, then clear their state on `terminal`; that extra start is absent from the retained output.

Preserve the original v38 11 completed rows and v39 27 completed plus one interruption (28 rows) as frozen outputs. They are not exhaustive accounting of every started hold. The [later #6343 lineage clarification](https://github.com/Unjuno/agent-interface/issues/6198#issuecomment-5942940480) recognizes the separate partial-admission start; no output from that posthoc scope extension is imported here.

## Verification and claims

Existing replay CI tests an unrelated scorer/scheduler replay module and does not independently validate these receipts. Historical tests and invocation counts are retained author reports, not newly executed results in this review. Recorded hashes were read, not recomputed.

The preserved claim is historical owner-commanded X11 interval-bound reproducibility only. It establishes no physical occupancy, exact ordinary key-up, useful feedback, causal comparison, live safety, game success, latency/product benefit, new observation, or independent duplicate replicate. Any exhaustive-start accounting requires separately scoped research.
