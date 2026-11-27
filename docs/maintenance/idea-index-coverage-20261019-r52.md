# Issue-index coverage audit r52 — 2026-10-19

This read compares the complete live r52 open-Issue set with exact primary table rows in `RESEARCH_ISSUE_INDEX.md` and `IDEAS_AND_OUTCOMES.md`; it does not count incidental mentions or predecessor references. Membership and ID hashes are in the [r52 snapshot](repository-inventory-20261019-r52.md).

| Exact route | Current open Issues | Meaning |
|---|---:|---|
| Primary row in `RESEARCH_ISSUE_INDEX.md` | 1,184 | Historical selected research inventory contains a direct primary row. |
| No primary row there | 489 | The 489 are exactly the r51 discovery queue after its two Issues #104 and #1798 closed; there are no new open IDs missing from that queue. All 489 have a direct route in one of the B01–B20 receipts. |
| Issue URL linked in `IDEAS_AND_OUTCOMES.md` | 685 | Curated outcomes, issue-family/successor cross-links, and eight new routing-only rows for IDs absent from both indexes. |
| Linked in either index | 1,673 | Every current open Issue reaches a primary research row or an issue URL in the curated idea index; no open Issue is missing from both. |

The immutable r51 queue had 491 entries. Its complete routing is preserved by the [B01–B20 receipt list](../WORKER_WORK_MAP.md) (B01–B19 contain 25 each; B20 contains 16). Before the new routing appendix, 38 queue items lacked a standalone first-column row in `IDEAS_AND_OUTCOMES.md`; 30 were already cross-linked from an issue/family/successor row. Eight still-open IDs (#2, #13–#17, #60, #61) had no issue URL in either index and now receive routing-only rows pointing to their B01/B02 receipts. The two queue entries now closed are #104 (`HOLD_GRID_TOO_COARSE`, no result upgrade) and #1798 (scoped durability request complete; parent #1769 remains open).

**Limit:** an index route is not semantic review, family prioritization, owner proof, PR disposition, evidence qualification, or permission to close an Issue. The 489 research-index omissions are discoverable and routed, but the historical research-selection table remains unchanged. Open PRs remain a separate 503-item inventory. Workers may take separate family/output paths in parallel; serialize only edits to the same shared index or map and verify resource ownership before any live allocation.
