# Repository membership recheck r160 — 2026-11-21

The paginated reads were bracketed by the same `main` SHA,
`f39e966b6478170a7a91f1eec7859d30046784bf`. The captured page sweep completed
around 2026-11-21 12:49 UTC; timestamp precision is minute-level.

| Set | r159 | r160 | Added | Removed | Exact current IDs | SHA-256 |
|---|---:|---:|---:|---:|---|---|
| Open Issues | 1,643 | 1,643 | 0 | 0 | [r152 CSV, reused after byte-identical comparison](open-issue-ids-20261121-r152.csv) | `2b878bf18f22dde388f76611c9c8ae317c70842aed3a06aaff26b66fb11e4aad` |
| Open PRs | 408 | 408 | 0 | 0 | [r157 CSV, reused after byte-identical comparison](open-pr-ids-20261121-r157.csv) | `c04ad73d08a79dec137ae1a7c87e9c1b6000ba092945e5d537ffa7beb9eb9f62` |

The complete ID lists were fetched from GitHub REST `issues?state=open&per_page=100`
and `pulls?state=open&per_page=100`. Issue-endpoint entries with a `pull_request`
field were excluded from the Issue set. Both ID sets were sorted numerically,
deduplicated, and compared byte-for-byte with r159; both comparisons were
identical. The lists use CRLF separators and a trailing CRLF, matching the r159
receipt encoding. Page counts were 20 full Issue pages plus 51 entries and an
empty terminal page; four full PR pages plus 8 entries and an empty terminal
page.

PRs #10402 and #10403 were opened and merged after r159. Their closed/merged
state was confirmed; neither is in r160's open set. This is membership evidence
only: it does not semantically classify the 2,051 open records, assign owners,
or reconcile branches, worktrees, ignored outputs, and raw-evidence custody.
No bulk closure follows from this snapshot. See the [JSON receipt](repository-inventory-recheck-20261121-r160.json).
