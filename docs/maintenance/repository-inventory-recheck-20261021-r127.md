# Repository membership recheck r127 — 2026-10-21

Captured at 2026-10-20 18:05 UTC against main `ef768ac74517d70c43c7b673b6ea4319db87d4f4`. Main was read before and after complete GitHub CLI pagination and remained unchanged. IDs were sorted numerically; hashes are SHA-256 over LF-joined decimal IDs with no trailing LF.

| Set | Current rows | Sorted-ID SHA-256 | Difference from r126 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 464 | `7ad4580e5175a6b5e64d773c249f12cdaadc895413a3ddc638d8a54ba7e95261` | #9310 added |

Commands: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number` and `gh pr list --repo Unjuno/agent-interface --state open --limit 1000 --json number`. Both returned complete sets. The open-PR addition is this cleanup-plan PR, #9310 (head `54cd90ab3`, base `main`). The open Issue set matches r126 exactly; the PR set is r126 plus #9310. No row metadata was duplicated. Fetch exact live records and dependencies before any state mutation.

This is a membership-only recheck. It does not classify the 1,655 open Issues or 464 PRs, establish PR readiness, confirm ownership, or resolve branch/worktree/raw-evidence custody. The worktree and idea-family backlogs remain separate.
