# Repository membership recheck r162 — 2026-11-22 JST

The complete paginated reads were bracketed by the same `main` SHA,
`ed0798d45d3bb7b839015619cd81f30e292a7583`. The r160 preserved sorted ID sets
were compared with fresh GitHub REST `issues?state=open&per_page=100` and
`pulls?state=open&per_page=100` results. Issue-endpoint rows with a
`pull_request` field were excluded from the Issue set.

| Set | r160 baseline | r162 | Added | Removed | Current set representation |
|---|---:|---:|---:|---:|---|
| Open Issues | 1,643 | 1,640 | 0 | 3 | [r152 sorted IDs](open-issue-ids-20261121-r152.csv) minus #7748, #7765, and #7817 |
| Open PRs | 408 | 407 | 0 | 1 | [r157 sorted IDs](open-pr-ids-20261121-r157.csv) minus #8181 |

The complete sets are derived from the immutable sorted r152/r157 CSVs by the
listed removals. Their canonical sorted decimal-ID representations with LF
terminators hash to `81a6c5a206fb2cd91a500124704d77c95a3135983da1be0a825aa7be661a4957`
(Issues) and `45245130443bf8e357cc3887e09d7a505861da9fdad0c404fb042e429f3539a2`
(PRs). No additions were found. The Issue removals are #7748 and #7765, both
closed after scoped evidence dispositions, and #7817, closed after its finite
T0 method result was reconciled with merged PR #7938. The only PR removal is
#8181, superseded after its packet was transferred through merged #10419.

This is a membership receipt, not complete semantic triage, branch/worktree
custody reconciliation, or permission to bulk-close issues. The r160 semantic
crosswalk remains the latest full routing analysis; targeted updates are linked
from the [current goal](../CURRENT_GOAL.md) and
[repository organization plan](../REPOSITORY_ORGANIZATION_PLAN.md). See the
[r161 receipt](repository-inventory-recheck-20261122-r161.md),
[r160 baseline](repository-inventory-recheck-20261121-r160.md), and
[machine-readable r162 summary](repository-inventory-recheck-20261122-r162.json).
