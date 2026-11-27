# Repository membership recheck r158 — 2026-11-21

Captured at 2026-11-21 12:14:04 UTC after PR #10400 merged. Complete paginated
reads of the open Issue and PR endpoints were bracketed by the same `main` SHA,
`db31eb235c202c8c44cab49056d8da9bd6a1d12b`.

| Set | r157 | r158 | Added | Removed | Exact current IDs | SHA-256 |
|---|---:|---:|---:|---:|---|---|
| Open Issues | 1,643 | 1,643 | 0 | 0 | [r152 CSV, reused after exact comparison](open-issue-ids-20261121-r152.csv) | `2b878bf18f22dde388f76611c9c8ae317c70842aed3a06aaff26b66fb11e4aad` for LF-separated IDs |
| Open PRs | 408 | 408 | 0 | 0 | [r157 CSV, reused after exact comparison](open-pr-ids-20261121-r157.csv) | `711a78f07a893f8fa5d930f293f138a0280b75d86efc7902ca278e9240208dd9` |

The exact before/after SHA, set hashes, and empty delta arrays are retained in
[the r158 JSON receipt](repository-inventory-recheck-20261121-r158.json).
The Issue endpoint was paginated with `issues?state=open&per_page=100` and
objects carrying a `pull_request` field were excluded. The PR endpoint was
paginated with `pulls?state=open&per_page=100`. IDs were sorted and deduplicated
before comparison.

PR #10400 was opened and merged between r157 and r158; neither snapshot
contains it, so the resulting open-set membership is unchanged. These counts
are membership evidence only. They do not semantically classify the 2,051 open
records, assign owners, or reconcile branches, worktrees, ignored outputs, and
raw-evidence custody. No bulk closure follows from this snapshot.
