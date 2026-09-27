# Issue #3212 source-lineage invalidation — 2026-09-20

Additive lifecycle experiment. Earlier records remain unchanged.

## H/T/D/C/U

- H: A receipt must fail closed when its source digest/lineage changes before effect; no XTEST input or DOM mutation may occur under the stale receipt.
- T: Three fresh Docker `--network none` allocations of `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, Xlib/XTEST, and read-only CDP DOM oracle. Each allocation first completed a valid receipt/effect, reset the fixture, then tested a source-lineage mismatch before running the valid replacement action.
- D: Source-lineage mismatch was `admitted=false` in 3/3. The post-denial DOM was `title=ReceiptFixture`, `saved=""`, `value=""` in 3/3, showing no input/effect under the stale receipt. The subsequent valid receipt effect passed in all allocations; session/resource/duplicate denials remained present; no `BadMatch` occurred.
- C: `PASS_CHROMIUM_SOURCE_INVALIDATION_FAIL_CLOSED_SCOPED`. This covers the declared fixture and digest mismatch only; it does not cover arbitrary source transformations, model cancellation, or production lineage storage.
- U: Add changed dependency/version, browser restart, cancellation, timeout, and orchestrator-restart rows to the same independent DOM/effect matrix.

## Raw summary

```json
{"runs":3,"source_mismatch_admitted":"0/3","source_mismatch_dom_unchanged":"3/3","valid_effect":"3/3","negative_cases_denied":"3/3","badmatch_runs":0,"formal_decision":"PASS_CHROMIUM_SOURCE_INVALIDATION_FAIL_CLOSED_SCOPED"}
```
