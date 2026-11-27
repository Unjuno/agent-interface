# Repository membership recheck r57 — 2026-10-19

Captured at `2026-10-19T02:37:22Z` from complete paginated `gh issue list`
and `gh pr list` results for `Unjuno/agent-interface`, against main
`d25b497cc8a05d45158a81c038ee15e03aabdddc` (after PR #8854 merged).

| Surface | Open count | SHA-256 of sorted numeric IDs (UTF-8, LF after each ID) | Full inventory |
|---|---:|---|---|
| Issues | 1,673 | `4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6` | [r57 Issues CSV](open-issues-20261019-r57.csv) |
| Pull requests | 501 | `b989d5a16e7347304e7f60adc5d8a6767e1967976735b1f92fde425aa1feba70` | [r57 PR CSV](open-prs-20261019-r57.csv) |

The Issue ID set hash matches r53–r56. The current PR count is one below r56;
the set hash above is newly computed from the complete live result. Each r57
CSV has one header plus one row per open object; read-back counts are 1,673 and
501 respectively.

The `updated_at` column is rendered in the capture host's local timezone,
Asia/Tokyo. Capture time in this note is UTC.

## Correction to earlier CSV paths

The checked-in `open-issues-20261019-r53.csv` and
`open-prs-20261019-r53.csv` currently contain only a PowerShell array-metadata
header (`Length`, `LongLength`, `Rank`, `SyncRoot`, `IsReadOnly`, `IsFixedSize`,
`IsSynchronized`, `Count`) and one array-summary row. They are not per-Issue or
per-PR inventories, and do not expose the sorted ID sets. Do not use them for
object-level triage or as the current full metadata export. They are left
unchanged as historical artifacts; r57 is the first corrected row-level
inventory linked from the current entry points.

This recheck establishes membership and the current CSV shape only. It does
not establish semantic classification, current worker ownership, branch or
worktree custody, merge readiness, or an Issue disposition. PR #8854's merge
does not complete Issue #59 or any live-control gate.
