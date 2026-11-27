# Repository membership recheck r138 — after #9356

Captured 2026-10-22 00:54:42 UTC against stable main `5a32f1e486b40103a1f24a6059ae78c8cb884e0f`; complete listings used GitHub CLI `--limit 5000` and the main SHA matched before and after.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` |
| Open PRs | 457 | `1b5b19cc5602a974b99345350207cca5a24c890d64661ba95f66aa6f0ca9d1f6` |

Exact ID sets: [Issues](open-issue-ids-20261022-r138.csv), [PRs](open-pr-ids-20261022-r138.csv). Hash is SHA-256 over numeric-sorted decimal IDs joined by LF without a trailing LF.

Compared with r137, Issue additions/removals: 0/0. PR additions/removals: 0/1. Removed PR IDs: `8827`. PR #9356 was opened and merged during the interval, so it has no net membership effect. #8827 was closed as superseded after #9356 integration. No other difference was observed.

Reuse the unchanged Issue row metadata and all unchanged PR row metadata from [r137](repository-inventory-recheck-20261022-r137.md). PR #8827's former row is historical; #9356 has no current open row because it merged. The r138 files above provide the complete current exact sets.

Membership does not establish semantic disposition, ownership, exact-head readiness, checks, evidence custody, or merge authorization. Refresh every record before state changes.

Commands: `gh api repos/Unjuno/agent-interface/git/ref/heads/main --jq .object.sha`; `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`.
