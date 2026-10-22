# Repository membership recheck r148 — after PR #8845

Captured 2026-10-22 against main `55ea8e991cd97a87c4a09016cec78caf821e92e7`.
Complete open Issue and PR reads finished with the same main SHA before and
after.

| Set | Rows | Exact ID CSV | CSV SHA-256 | Comparison with r145 |
|---|---:|---|---|---|
| Open Issues | 1,654 | [IDs](open-issue-ids-20261022-r148.csv) | `8e2c08331f735f9d8bd004c715515886aa3a46ec77a0fc5c4e178e4b7c88aa59` | Exact ID set |
| Open PRs | 452 | [IDs](open-pr-ids-20261022-r148.csv) | `2d938f6e72e337ac69ed6d5586576e762bb2b6741ea118a532f2a1ff46024c6d` | r145 minus #8845 |

The records were fetched with `gh issue list --state open --limit 5000 --json
number` and `gh pr list --state open --limit 5000 --json number`. The CSV files
contain the complete sorted ID sets. Their SHA-256 values cover the exact
committed Git blob bytes (UTF-8 CSV with LF line endings), including the
`number` header. The Issue membership
exactly matches r145. PR #8845 is the only ID removed from r145; its merge
commit is `55ea8e991cd97a87c4a09016cec78caf821e92e7`, and its live PR record
has no closing Issue references. No Issue membership changed.

Membership only establishes discovery. It does not establish semantic
disposition, exact-current PR readiness, owner, assignment, or artifact
custody. Re-fetch each touched record before a later state change. This batch
did not use WSLc or Docker; the already completed WSLc experiment inside #8845
was not repeated.
