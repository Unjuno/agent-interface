# Repository membership recheck r155 — 2026-11-21

Captured during the 2026-11-21 UTC work session. Remote `main` was
`63449e8abed5938a780de22cabc160aefd9d3326` before and after the complete
paginated REST reads.

| Set | r152 | r155 | Added | Removed | Exact sorted ID set | SHA-256 |
|---|---:|---:|---:|---:|---|---|
| Open Issues | 1643 | 1643 | 0 | 0 | [r152 CSV, reused because IDs match](open-issue-ids-20261121-r152.csv) | `9a2abc9b02c2ca9eabd17c5874e974d0b4804f92589601eee7dcd0ecc08e1f79` |
| Open PRs | 410 | 409 | 0 | 1 | [r155 CSV](open-pr-ids-20261121-r155.csv) | `f5cef936514a5f1483bb336847795fbbef416a92996bb53da8221c9e5c08891c` |

The Issue read used paginated `issues?state=open&per_page=100` and excluded
objects with `pull_request`; the PR read used paginated
`pulls?state=open&per_page=100`. Exact ID comparison found #10218 as the sole
removed PR. PR #10377 was opened and merged during this interval, so it has no
remaining membership effect. The r155 PR ID file is derived from the prior
r152 sorted set by removing the one live-confirmed delta.

PR #10218 is closed unmerged as superseded, with its source branch retained.
Its late-usage code was transferred to #10352 (merged as `b0493167`), and its
test scheduling/cleanup repair is in #10365 (merged as `897f4896`). Current
main has the spool publisher, provider-attempt recorder method, and public
caller method. These are deterministic synthetic adapters; they do not
establish automatic invocation by all callers or live provider accounting.

This is membership evidence only. It does not classify hypotheses, establish
custody, or determine merge readiness. No bulk Issue or PR action follows from
this snapshot. Issue #57 and Issue #58 remain open; the live WSLc migration STOP
and the allocation/resource holds retain their own release conditions.
