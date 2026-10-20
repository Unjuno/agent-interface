# Repository membership recheck r124 — 2026-10-21

Captured after PR #9300 merged and stale-base PR #8844 was closed. `main` was `e45ca89a3f7bf1b8a7cf5701454b751e0a53e9f3` before and after complete paginated `gh issue list --limit 2000` and `gh pr list --limit 1000` reads.

| Set | Current rows | Sorted-ID SHA-256 | Difference from full r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `720d98407db3844e421e3e647bfec33889e90e842d1d3bd4b601c2db93a4faa9` | None |
| Open PRs | 463 | `2cc4641ad5a3a2d70fd1e5d1c34741d2b081ffaca352439c88c554033994bbee` | #8841, #8733, #8716, and #8844 only |

The Issue set exactly matches r120; the PR set exactly matches r120 minus #8841, #8733, #8716, and #8844. PR #9300 was opened and merged between reads and is absent from the open set. PR #8844 was closed only after merged successor #9300 preserved its 21 evidence blobs and a read-only check verified all 2,198 archive files against the manifest. Its source branch remains. Issue #8636 stays open for its distinct transfer question. This is a membership recheck, not semantic disposition, exact readiness review, ownership, or artifact-custody proof.
