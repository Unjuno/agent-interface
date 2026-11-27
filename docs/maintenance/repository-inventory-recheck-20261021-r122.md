# Repository membership recheck r122 — 2026-10-21

Captured at 2026-10-20 16:01 UTC against `main` `b3a44eb1f33c59b848b6361b95787b8edf991aab`. The main OID was identical before and after complete paginated CLI reads (`gh issue list --limit 2000`, `gh pr list --limit 1000`).

| Set | Current rows | Sorted-ID SHA-256 | Difference from full r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `720d98407db3844e421e3e647bfec33889e90e842d1d3bd4b601c2db93a4faa9` | None |
| Open PRs | 465 | `09f3051f32c565068bdd7ae10b6671a535780eb7ae6e9cb9cc72e5551401ec5e` | #8841 and #8733 only |

The full r120 row exports remain reusable: the Issue set is unchanged and the PR set equals r120 minus #8841 and #8733. PR #9293 was opened and merged between the r121 and r122 reads, so it is absent from both open sets. PR #8733 was closed as superseded only after merged successor #9293's 27 evidence blobs and all 17 manifest entries were verified on main; its source branch remains. This recheck establishes membership only, not semantic disposition, exact PR readiness, ownership, or workspace custody.

**Same-set follow-up:** after PR #9294 merged and the #8641 body received its catalog backlink, a complete read at main `c27257409cef5acf97be1b10e88762176d648bd2` again returned 1,655 Issues / 465 PRs, with the SHA unchanged before and after. Both current ID sets exactly match r122. The opened-and-merged #9294 left no open-set change.
