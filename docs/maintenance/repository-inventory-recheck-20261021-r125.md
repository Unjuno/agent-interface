# Repository membership recheck r125 — 2026-10-21

Captured after PR #9303 merged. `main` was `99cdd7072c718ac410de21a3a471ee6cb0e1f337` before and after complete paginated `gh issue list --limit 2000` and `gh pr list --limit 1000` reads. The live sets were compared with the complete row-level r120 metadata.

| Set | Current rows | SHA-256 of sorted numeric IDs joined by LF, no trailing LF | Difference from r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 463 | `3c1290839220a5c5274f3ca638aad310efa484b0eaa11dcf092d8c29931ca676` | #8716, #8733, #8841, #8844, and #9303 only |

Issue membership exactly matches r120. PR #9303 was opened and merged during this cleanup batch and is absent from the current open set. The open-PR ID set is exactly r120 minus #8716, #8733, #8841, #8844, and #9303; there were no additions. Reuse r120's row-level metadata for unchanged IDs, but re-fetch every touched record before disposition. This is a membership recheck only, not semantic triage, current PR readiness, ownership, or custody proof.
