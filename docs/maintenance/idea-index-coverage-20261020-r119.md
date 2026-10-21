# Issue idea-index coverage r119 — 2026-10-20

Baseline: complete open Issue set r119 at main `666888468e81b3c3c2c1e4103df549afcaf23822`; the live ID set was rechecked against r118 and matched exactly. The reproducible inputs are the [r119 inventory](repository-inventory-recheck-20261020-r119.md), [open-Issue metadata](open-issues-20261020-r119.json), `RESEARCH_ISSUE_INDEX.md`, `IDEAS_AND_OUTCOMES.md`, and literal exact-URL scans of `docs/ideas/*.md`.

## Coverage counts

| Route | Open Issues | Interpretation |
|---|---:|---|
| Direct primary row in the Issue inventory table of `RESEARCH_ISSUE_INDEX.md` | 1,184 | Historical research inventory row exists. |
| No primary row in `RESEARCH_ISSUE_INDEX.md` | 488 | Discovery/crosswalk work remains; not evidence of missing idea or permission to close. |
| Exact Issue URL appears in `IDEAS_AND_OUTCOMES.md` | 685 | Central curated page routes the Issue; this does not prove family-level semantic reconciliation. |
| Linked in either central index | 1,672 | All current open Issues have at least one central route. |
| Missing from both central indexes | 0 | None. |
| Missing primary row but exact URL occurs in a `docs/ideas/*.md` file | 223 | Literal local file route exists; some files may be audits/agendas, not a canonical family record. |
| Missing primary row and no exact URL in any `docs/ideas/*.md` | 265 | Finite family-disposition candidate queue below. |

The [family-disposition queue](open-issues-without-family-record-20261020-r119.csv) contains 265 live candidates in eleven disjoint number-sorted batches D01–D11 (25 Issues per batch except the final remainder). Every candidate appeared in a previous r51 discovery batch; the CSV links that receipt so workers can reuse prior reading and check only changes since its `updatedAt`. The three r51 entries no longer in the current missing-primary set are #104, #1798, #8574: #104 and #1798 are no longer open, and #8574 now has a primary row.

## Interpretation and limits

These counts describe navigation only. A literal link may be a citation, audit, successor, or agenda reference rather than an idea-family disposition. The 223 exact URL matches across 132 idea documents therefore still require semantic review where no canonical family link is clear. The 265 candidates are not “bad Issues”; each may be a distinct experiment, failure, result, dependency, or idea that should be preserved. The queue is sorted and split only for nonoverlapping discovery outputs; related issues can cross batch boundaries. A worker must report such joins but cannot edit shared indexes or change Issue/PR state.

No Issue was closed by this audit. Use each prior B01–B20 receipt as first-pass context, re-read the current Issue when `updatedAt` or referenced evidence changed, then write only to `docs/maintenance/idea-family-triage-r119/Dxx.md`. One integrator turns reviewed batches into family records and shared-index edits serially.
