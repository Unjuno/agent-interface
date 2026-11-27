# Issue-index coverage audit r51 — 2026-10-19

This bounded reconciliation joins the complete [r51 open-Issue membership snapshot](repository-inventory-20261019-r51.md) to canonical GitHub Issue links in the primary `Issue inventory` table of `docs/RESEARCH_ISSUE_INDEX.md` and to exact URL mentions in individual `docs/ideas/*.md` files. It measures navigation only; it does not classify meaning, priority, ownership, completion, or closure eligibility.

| Check | Result |
|---|---:|
| Open Issues in r51 | 1,675 |
| Distinct primary Issue rows in the research index | 1,729 |
| r51 open Issues with a primary row | 1,184 |
| r51 open Issues absent from primary rows | 491 |
| Of missing rows, exact URL appears in an individual `docs/ideas/*.md` file | 220 |
| Of missing rows, no exact URL appears in an individual `docs/ideas/*.md` file | 271 |

The [r51 work queue](open-issues-missing-research-primary-row-20261019-r51.csv) preserves every missing Issue’s current snapshot metadata and splits the number-sorted list into 20 disjoint batches of at most 25 rows (`B01`–`B20`). `exactDocsIdeasUrlMention` and `docsIdeasFiles` report literal link presence only. They are not semantic family assignment. `routingBatch` is collision-free bookkeeping, not topic classification. Re-read the live Issue and linked evidence before changing any shared family record, owner, or state.

## How to work the queue

1. A worker claims one batch or one explicitly named family, records its Issue numbers and a unique additive output path, and checks live status and existing ownership first. Do not take overlapping rows from a batch already claimed.
2. For each Issue, read the body, relevant current comments, linked PR diffs and retained evidence. Record the falsifiable question, distinct hypotheses, actual first result, limits, related family (if demonstrated), and one finite next discriminator. A URL mention, label, title, or index row is only a discovery clue.
3. One integrator at a time updates the shared index and work map. Family research may proceed concurrently in disjoint files. Keep unresolved candidates in the queue; do not close Issues to reduce counts.
4. After each bounded batch, preserve decisions and citations in the family entry, then regenerate a new dated snapshot only when membership changes. Never edit this captured queue in place.

## Reproduction and bounds

The inventory was captured at `2026-10-19T00:20:08Z` against main `0dafeff35e73316216c95d37f9f7e799bf8a21a8`. The primary set was parsed only from canonical Issue URLs beneath the exact `## Issue inventory` heading, and the idea-file set from literal canonical GitHub Issue URLs in tracked `docs/ideas/*.md` files at that ref. The old r15 audit and queue remain immutable. This is a navigation-coverage audit, not a claim that all 1,675 items are research ideas; any candidate can be engineering, coordination, duplicate, transfer, or other work.
