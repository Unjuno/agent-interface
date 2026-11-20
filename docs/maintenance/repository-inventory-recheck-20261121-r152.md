# Repository membership recheck r152 — 2026-11-21

Captured at 2026-11-20T16:55:55Z UTC. Remote `main` was `bab0b6fd18a8c64fbc664476ebbf26ef2267f7d7` immediately before and after both paginated membership reads.

| Set | r151 | r152 | Added | Removed | Exact ID set | SHA-256 | Delta |
|---|---:|---:|---:|---:|---|---|---|
| Open Issues | 1654 | 1643 | 0 | 11 | [CSV](open-issue-ids-20261121-r152.csv) | `9a2abc9b02c2ca9eabd17c5874e974d0b4804f92589601eee7dcd0ecc08e1f79` | [CSV](open-issue-delta-20261121-r152.csv) |
| Open PRs | 452 | 410 | 11 | 53 | [CSV](open-pr-ids-20261121-r152.csv) | `e45999de7c23544afa0ce875a29a999ae34bbbe4beb2285fc123614e48c3e64b` | [CSV](open-pr-delta-20261121-r152.csv) |

Issue membership used the paginated GitHub REST endpoint `issues?state=open&per_page=100`, filtering out pull-request objects. PR membership used `gh pr list --state open --limit 5000 --json number`. Each ID CSV is sorted by numeric ID and uses UTF-8/LF; hashes cover exact committed bytes.

This is a membership snapshot, not semantic triage, ownership/custody validation, or merge readiness. The previous r151 receipt had only ID sets, so this comparison records membership additions/removals only; unchanged records still require a live read when selected for action. No Issues were bulk-closed.

Since the previous snapshot, PRs #10354, #10352, and #10353 were merged after current-main evidence checks. Issue #57 remains open. PR #10340 remains draft on old base `86a52662dc2bb690dd670d52ea8d97816aef2a26`; local rebase was aborted after the local clone failed to find a common merge base and began replaying unrelated history. No PR #10340 source or remote state was changed.
