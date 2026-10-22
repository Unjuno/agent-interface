# Repository membership recheck r126 — 2026-10-21

Captured against `main` `d3439cb9adee0bd64492d5378c05568357d38d56`. The main ref was read before and after complete paginated GitHub CLI reads and was unchanged. Issue and PR IDs were sorted numerically; hashes are SHA-256 of the LF-joined decimal IDs with no trailing LF.

| Set | Current rows | Sorted-ID SHA-256 | Difference from full r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 463 | `3c1290839220a5c5274f3ca638aad310efa484b0eaa11dcf092d8c29931ca676` | #8716, #8733, #8841, and #8844 only |

Commands: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number` and `gh pr list --repo Unjuno/agent-interface --state open --limit 1000 --json number`; each returned the full set. Reusing r120's row exports is valid because the live Issue ID set is identical and each open PR difference is explicit. Re-fetch each touched record before any state change.

**Correction to r125's prose:** r125 listed #9303 as an additional PR-set removal, but the full r120 PR export does not contain #9303, and r126's independently recomputed IDs match r120 minus the four PRs shown above. The r125 count and hash match r126; this corrects its difference list without altering the historical r125 record.

This is a membership recheck only. It does not establish semantic triage, current PR readiness, ownership, or branch/worktree/raw-evidence custody.
