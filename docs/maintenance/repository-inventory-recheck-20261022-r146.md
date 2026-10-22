# Repository membership recheck r146 — after PR #9373

Captured 2026-10-22 03:53 UTC against `main` `0ba19dc885d9531e6fc21c5ea9e26a624fb25bca`. Complete open Issue and PR reads finished with the same main SHA before and after.

| Set | Rows | Sorted-ID SHA-256 | Comparison |
|---|---:|---|---|
| Open Issues | 1,654 | `f72384f45b9f90d5e8f9e68927f98320c3398641716f8b58f69525ccc58ece21` | Exact ID sequence equals r145 |
| Open PRs | 453 | `17b5b07e90a662f1feb42d730673c6d1bb90eee7453c27e98e308a34fb8170d1` | Exact ID sequence equals r145 |

The r145 ID files are reused because the current fully paginated sets were compared row-for-row with them and are identical: [open Issues](open-issue-ids-20261022-r145.csv), [open PRs](open-pr-ids-20261022-r145.csv). The comparison used sorted, unique numeric IDs; counts matched source row counts. This recheck follows PR #9373, which opened and merged without a net membership change. It does not establish semantic disposition, PR readiness, current ownership, or artifact custody.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`. Before/after main SHA: `0ba19dc885d9531e6fc21c5ea9e26a624fb25bca`.

No WSLc/Docker allocation or container operation was used.
