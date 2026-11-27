# Open Issue inventory refresh — 2026-10-17

At 2026-10-17 01:48 UTC, a paginated GitHub REST read of open Issues (excluding pull-request objects) returned 1,677 Issues, numbers 2–9004. The current metadata snapshot is [open-issues-20261017-r4.csv](open-issues-20261017-r4.csv); it records number, title, URL, update time, labels, and assignees. This is an inventory, not a review of all 1,677 bodies or proof that all ideas are organized.

Compared with [r3](open-issues-20261016-r3.csv), the set changed by three IDs:

- Added to open: [#9004](https://github.com/Unjuno/agent-interface/issues/9004), whose existing agreement-conditioned continuation note is indexed in [`docs/ideas/README.md`](../ideas/README.md).
- No longer open: [#2577](https://github.com/Unjuno/agent-interface/issues/2577) and [#6873](https://github.com/Unjuno/agent-interface/issues/6873); each was individually read back as CLOSED.

The 2026-10-17 [open-Issue citation audit](../ideas/open-issue-citation-audit-20261017.md) covers the original 49 Issues that lacked direct Markdown citations in its bounded comparison plus 12 more found in a follow-up live recheck. A full open-Issue link scan found no citation omissions, but neither that audit nor this metadata snapshot certifies complete semantic triage of all 1,677 Issue bodies. Reconcile by theme and current evidence before closing, merging, or deleting anything.

The paginated API read is not atomic across pages. It is a dated navigation snapshot; query current Issue state before any consequential disposition.
