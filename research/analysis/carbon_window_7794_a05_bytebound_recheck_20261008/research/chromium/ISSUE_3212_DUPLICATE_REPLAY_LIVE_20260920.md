# Issue #3212 — live duplicate/replay receipt rejection (2026-09-20)

Additive replay-safety evidence. Prior artifacts and broader HOLDs remain unchanged.

## H/T/D/C/U

- **H:** A receipt that has already produced an application effect must not be admitted again when replayed; the second attempt must leave the DOM unchanged.
- **T:** Three real Docker `--network none` allocations using `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, CDP DOM observation, and the same receipt-bound fixture runner. Each allocation dispatched one receipt once, then replayed the identical receipt.
- **D:** `PASS_DUPLICATE_REPLAY_AUDIT rows=3 errors=0`. First effect `3/3` (`title=saved:first`, `saved=true`, `value=first`); replay admission `0/3`; replay DOM unchanged `3/3`. Raw SHA-256: `4c4d5fb27e218822f64e073905ea12ebbcd4537b52e99134aa49c19e386c17f9`.
- **C:** `PASS_CHROMIUM_DUPLICATE_REPLAY_FAIL_CLOSED_SCOPED`. The tested receipt cannot produce a second effect in this live fixture.
- **U:** This covers the declared duplicate receipt path only; it does not prove all transport-level replay, cross-process replay, or model-wait benefit. Existing full-issue HOLDs remain.

Runner, fixture, raw trace, and independent auditor are under `research/chromium/issue-3212-duplicate-replay-v1/`.
