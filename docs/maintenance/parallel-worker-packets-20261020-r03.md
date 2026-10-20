# Parallel worker packets r03 — 2026-10-20

Baseline: `main` at `666888468e81b3c3c2c1e4103df549afcaf23822`. The complete
[r119 inventory](repository-inventory-recheck-20261020-r119.md) contains 1,672
open Issues and 468 open PRs; both exact ID sets match r118, while full row
metadata was refreshed. The latest
[idea-index coverage audit](idea-index-coverage-20261020-r119.md) finds 488
open Issues without a primary research-index row. All 488 are linked from
`IDEAS_AND_OUTCOMES.md`, so no current open Issue is absent from both central
indexes. Of the 488, 223 have a literal URL in `docs/ideas/*.md`; the other 265
form the [family-disposition queue](open-issues-without-family-record-20261020-r119.csv).

The queue has eleven disjoint number-sorted discovery slices, D01–D11. Each
entry also names its prior B01–B20 read receipt so a worker can reuse existing
source review and refresh only when `updatedAt`, evidence links, or live state
changed. The D labels partition private output paths; they do not assign
workers, identify semantic families, reserve resources, or authorize Issue
state changes. Related Issues can cross the numeric boundaries.

## Disjoint family-disposition discovery packets

| Packet | Rows | First–last Issue | Private output | Boundary |
|---|---:|---:|---|---|
| D01 | 25 | #12–#187 | `docs/maintenance/idea-family-triage-r119/D01.md` | Discovery only; link cross-batch siblings. |
| D02 | 25 | #199–#344 | `docs/maintenance/idea-family-triage-r119/D02.md` | Discovery only; link cross-batch siblings. |
| D03 | 25 | #345–#672 | `docs/maintenance/idea-family-triage-r119/D03.md` | Discovery only; link cross-batch siblings. |
| D04 | 25 | #706–#1,631 | `docs/maintenance/idea-family-triage-r119/D04.md` | Discovery only; link cross-batch siblings. |
| D05 | 25 | #1,635–#3,447 | `docs/maintenance/idea-family-triage-r119/D05.md` | Discovery only; link cross-batch siblings. |
| D06 | 25 | #3,544–#6,624 | `docs/maintenance/idea-family-triage-r119/D06.md` | Discovery only; link cross-batch siblings. |
| D07 | 25 | #6,640–#7,160 | `docs/maintenance/idea-family-triage-r119/D07.md` | Discovery only; link cross-batch siblings. |
| D08 | 25 | #7,162–#7,470 | `docs/maintenance/idea-family-triage-r119/D08.md` | Discovery only; link cross-batch siblings. |
| D09 | 25 | #7,475–#8,522 | `docs/maintenance/idea-family-triage-r119/D09.md` | Discovery only; link cross-batch siblings. |
| D10 | 25 | #8,525–#8,619 | `docs/maintenance/idea-family-triage-r119/D10.md` | Discovery only; link cross-batch siblings. |
| D11 | 15 | #8,620–#8,913 | `docs/maintenance/idea-family-triage-r119/D11.md` | Discovery only; link cross-batch siblings. |

Ranges show the lowest and highest Issue number in each slice; the CSV is the
authoritative exact member list. Do not assume every number in a range belongs
to the packet.

## Worker output contract

Before beginning a packet, verify that no active worker is already writing its
private output and refresh the live Issue/PR state for its rows. Use the linked
B receipt as context. Re-read the Issue body/comments only when the source or
evidence changed since that receipt. For each row, record one of:

- a canonical family record and the specific hypothesis/result it covers;
- a distinct idea needing a new family crosswalk;
- an audit, successor, dependency, coordination, or implementation record
  whose role is not itself a separate research hypothesis; or
- unresolved classification with the precise missing evidence.

Link the first outcome and immutable raw evidence, scope limits, relevant PRs
and dependencies, current ownership conflicts, and one finite next decision.
Do not promote a result from a title or literal URL alone. Report any related
Issue in a different D packet so the integrator can reconcile the family once.
Workers write only their D file; they do not edit the shared research indexes,
idea catalog, work map, this packet list, or Issue/PR state.

One integrator reviews the D outputs and current source, then updates the
canonical family file and shared indexes serially. Keep the Issue open if its
distinct question, evidence gap, or dependency remains. Close only after its
own work is complete or transferred, the idea/result is preserved, and both
source and return links are verified. Physical cleanup and live allocations
are outside these discovery packets.

The five still-open PRs in the
[nine-PR disposition receipt](pr-audit-disposition-20261020-r01.md) remain a
separate track: #8836 cost accounting, #8841 construction evidence, #8844 A04
audit custody, #8702 raw custody, and #8845 shared-lane ownership. Do not use
these discovery slices to infer that any PR is ready to merge or close.
