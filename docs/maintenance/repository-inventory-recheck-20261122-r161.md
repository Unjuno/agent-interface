# Repository membership recheck r161 — 2026-11-22 JST

The complete paginated reads were bracketed by the same `main` SHA,
`f75b34bc00b125c8cb6f106ea43835cea1401e2e`. r160's preserved sorted ID sets
were compared with fresh GitHub REST `issues?state=open&per_page=100` and
`pulls?state=open&per_page=100` results. Issue-endpoint rows with a
`pull_request` field were excluded from the Issue set.

| Set | r160 | r161 | Added | Removed | Current set representation |
|---|---:|---:|---:|---:|---|
| Open Issues | 1,643 | 1,641 | 0 | 2 | [r152 sorted IDs](open-issue-ids-20261121-r152.csv) minus #7748 and #7765 |
| Open PRs | 408 | 407 | 0 | 1 | [r157 sorted IDs](open-pr-ids-20261121-r157.csv) minus #8181 |

The baseline sets are reused without copying: r160 confirmed them byte-identical
to r159, and r161 compared their exact IDs against the fresh complete page
sweeps. The only Issue removals are #7748 and #7765, both closed after their
finite evidence-backed dispositions. The only PR removal is #8181, closed as
superseded after the T0d evidence packet was transferred through merged #10419.
No new open Issue or PR appeared.

PR #10418 was opened after r160 and merged into this `main` as `f75b34b`; it is
not an r160 member and has no open-set effect. Its merge incorporated the
current targeted B13 dispositions and the #8859 trace-classification feasibility
audit. Issue #57 and Issue #8859 remain open. This receipt is membership
evidence, not semantic triage, owner/custody reconciliation, or a reason for
bulk closure. See the [machine-readable receipt](repository-inventory-recheck-20261122-r161.json),
[r160 baseline](repository-inventory-recheck-20261121-r160.md), and the
[r160 semantic crosswalk](idea-index-crosswalk-20261121-r160.md).
