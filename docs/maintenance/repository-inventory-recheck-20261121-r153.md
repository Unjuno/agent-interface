# Repository membership recheck r153 — 2026-11-21

Captured between `2026-11-20T20:19:58Z` and `2026-11-20T20:20:37Z` UTC.
Remote `main` was `cfb691b3b890d01c0b24fd1cd988609a62c4dd2a` immediately
before and after both paginated GitHub REST membership reads.

| Set | r152 | r153 | Added | Removed | Exact sorted ID set | SHA-256 |
|---|---:|---:|---:|---:|---|---|
| Open Issues | 1643 | 1643 | 0 | 0 | [r152 CSV](open-issue-ids-20261121-r152.csv) | `9a2abc9b02c2ca9eabd17c5874e974d0b4804f92589601eee7dcd0ecc08e1f79` |
| Open PRs | 410 | 410 | 0 | 0 | [r152 CSV](open-pr-ids-20261121-r152.csv) | `e45999de7c23544afa0ce875a29a999ae34bbbe4beb2285fc123614e48c3e64b` |

The exact sorted membership is unchanged, so r153 reuses the r152 ID files and
does not add duplicate CSVs. The paginated read used
`issues?state=open&per_page=100` with pull-request objects excluded, and
`pulls?state=open&per_page=100`. PR #10361 was created and merged between the
r152 and r153 snapshots; the final open membership is identical.

This is membership evidence only. It does not classify hypotheses, establish
custody, or determine merge readiness. No bulk Issue or PR action follows from
this unchanged snapshot. No action was taken on #57, #5130, #7924, #908, or
other tracker records during this read.
