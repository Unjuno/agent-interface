# Repository membership recheck r157 — 2026-11-21

Captured after PR #10340 merged. The complete paginated GitHub REST reads were
bracketed by the same `main` SHA, `9734c7f907b49799c134483d6011d092f190740d`
(2026-11-21 11:53:58 UTC).

| Set | r155 | r157 | Added | Removed | Exact current IDs | SHA-256 |
|---|---:|---:|---:|---:|---|---|
| Open Issues | 1,643 | 1,643 | 0 | 0 | [r152 CSV, reused after exact set comparison](open-issue-ids-20261121-r152.csv) | `2b878bf18f22dde388f76611c9c8ae317c70842aed3a06aaff26b66fb11e4aad` for LF-separated IDs |
| Open PRs | 409 | 408 | 0 | 1 | [r157 CSV](open-pr-ids-20261121-r157.csv) | `711a78f07a893f8fa5d930f293f138a0280b75d86efc7902ca278e9240208dd9` |

Issue IDs are unchanged from r155/r152. The only PR membership change is
#10340, which merged as the pinned `main` commit above. The exact API receipt,
including both endpoint SHA brackets and set deltas, is retained in
[r157 JSON](repository-inventory-recheck-20261121-r157.json).

The Issue read paginated `issues?state=open&per_page=100` and excluded records
with a `pull_request` field; the PR read paginated
`pulls?state=open&per_page=100`. IDs were sorted and deduplicated before
comparison. The separate r156 read on main `96c878dae64302b1a02e9b9377c018ad599d6fcc`
matched r155 exactly; r157 then showed only #10340 removed. No Issue or PR was
closed to make the counts smaller.

This is membership evidence only. It does not semantically classify 2,051 open
records, assign owners, or reconcile branches, worktrees, ignored outputs, and
raw-evidence custody. The next cleanup wave remains bounded semantic routing and
custody reconciliation from the existing family indexes and worker map. No
bulk closure follows from this snapshot.
