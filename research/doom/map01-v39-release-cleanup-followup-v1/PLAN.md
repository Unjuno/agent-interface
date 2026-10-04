# Cleanup receipt validation follow-up

## H/T/D/C/U

- **H:** The PR #7385 cleanup classifier may preserve an ordinary-release PASS when owner history or the caller's release bracket is malformed.
- **T:** Add three adversarial regressions for an `owner_release` with a missing timestamp, a non-dictionary history row, and a missing caller start time. Run them against the exact parent source, then run the repaired backend suite and adjacent owner-wrapper suite.
- **D:** The parent must fail all three regressions; the candidate must pass all three plus both complete suites. The persisted exit receipts and terminal unittest summaries must agree.
- **C:** This checks deterministic synthetic receipts, not actual X11 delivery, physical key state, application feedback, or a live allocation.
- **U:** A malformed log fails closed. The historical PR #7385 candidate result remains tied to its parent source and is not evidence for this follow-up source.

## Frozen parent

Parent commit: `2834209601483503a316863cf9964c9f966cede5` (the exact PR #7385 head before this repair).

The predecessor package's source digest is retained in its original `SHA256SUMS`; this follow-up leaves that package untouched.

After the stacked parent advanced, the three regressions were rerun against its exact new head `90e65c932a8a487d9657713e5a243cba25125c4f`; all three still failed before the repair. The follow-up branch was rebased onto that head, and the candidate suites were rerun there.
