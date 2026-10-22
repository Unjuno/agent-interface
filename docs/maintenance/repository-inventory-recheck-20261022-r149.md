# Repository membership recheck r149 — after PR #9397

Captured 2026-10-22 against main `b0e8c6c9b4cfb7917932f52e7a69d8267348aa89`. Complete open Issue and PR membership reads were bracketed by the same remote main SHA.

| Set | Rows | Exact ID CSV | SHA-256 |
|---|---:|---|---|
| Open Issues | 1,654 | [IDs](open-issue-ids-20261022-r149.csv) | `8e2c08331f735f9d8bd004c715515886aa3a46ec77a0fc5c4e178e4b7c88aa59` |
| Open PRs | 452 | [IDs](open-pr-ids-20261022-r149.csv) | `2d938f6e72e337ac69ed6d5586576e762bb2b6741ea118a532f2a1ff46024c6d` |

The reads used `gh issue list --state open --limit 5000 --json number` and `gh pr list --state open --limit 5000 --json number`, sorted by numeric ID. The SHA-256 values cover the exact committed Git blob bytes (UTF-8 CSV with LF line endings). Compared with r148: Issues added none, removed none; PRs added none, removed none. These are membership deltas only and do not establish semantic disposition, ownership, custody, or merge readiness. Refresh every record before changing its state.

PR #9397 merged at this main SHA. The merge did not establish a complete semantic queue audit. PR #8800 remains open on the specific A14 raw-custody hold; see [its custody comment](https://github.com/Unjuno/agent-interface/pull/8800#issuecomment-6334524921). No A14 run was repeated. This recheck used no WSLc or Docker allocation.
