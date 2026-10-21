# Repository membership recheck r123 — 2026-10-21

Captured after PR #9296 merged and stale-base PR #8716 was closed. `main` was `770914137fb0fad44f14918c8303e733c7d1624f` before and after complete paginated `gh issue list --limit 2000` and `gh pr list --limit 1000` reads.

| Set | Current rows | Sorted-ID SHA-256 | Difference from full r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `720d98407db3844e421e3e647bfec33889e90e842d1d3bd4b601c2db93a4faa9` | None |
| Open PRs | 464 | `ca43fba486d59e0c298aad5cda0794d3ba30f39c6b702441e8a0c8974e6b04d8` | #8841, #8733, and #8716 only |

The Issue set exactly matches r120; the PR set exactly matches r120 minus #8841, #8733, and #8716. PR #9296 was opened and merged between reads, so it is absent from the open set. PR #8716 was closed only after merged successor #9296 preserved all 13 evidence blobs byte-for-byte and all nine packet manifest hashes. The source branch remains. Issue #8620 stays open for its distinct transfer/evaluation question. This is a membership recheck, not semantic disposition, exact readiness review, ownership, or artifact-custody proof.

**Same-set follow-up:** after docs-only PR #9297 merged, a second pair of complete paginated reads at main `7453b7ad914984e2f53e76149afb27cec1081e59` found the same 1,655 Issue IDs and 464 PR IDs. Both sorted-ID hashes remain unchanged, confirming that the new documentation PR left the open sets unchanged.
