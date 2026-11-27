# Idea-index coverage audit r15 — 2026-10-19

This read-only reconciliation joins the paginated [r15 open-Issue inventory](repository-inventory-20261019-r15.md) to the primary rows under the Issue inventory section of RESEARCH_ISSUE_INDEX.md and to exact Issue-URL mentions in individual docs/ideas family entries. It checks navigation coverage, not Issue meaning.

| Check | Result |
|---|---:|
| Current open Issues | 1675 |
| Distinct primary Issue rows in the research index | 1729 |
| Current open Issues with a primary row | 1184 |
| Current open Issues absent from primary rows | 491 |
| Of the missing rows, exact Issue URL appears in a family entry | 220 |
| Of the missing rows, no exact Issue URL appears in an individual family entry | 271 |
| Historical primary rows not currently open | 545 |

The bounded [missing-primary-row list](open-issues-missing-research-primary-row-20261019-r15.csv) is sorted by Issue number and hashes to 7216493d01a5a88b4126eb1821e702ecd3adaff64954154d9227b20801b4b7a4. Its family-entry flag means only that an exact URL is present somewhere in that file; it does not mean the Issue has been semantically reconciled, is active, is complete, or can be closed. Every row therefore remains marked untriaged.

**Interpretation:** the research index is a useful historical discovery selection, not a current all-open-Issue ledger. A 491-row mismatch includes old foundational Issues, newer families, and possible non-research work; do not mass-import them as research or mass-close them. Begin with a small, coherent family: read current bodies/comments and linked PR/evidence; confirm whether a canonical family record exists; state the distinct hypothesis, retained PASS/FAIL/STOP, evidence/custody limits, and one next discriminator or reasoned disposition. Update one family entry and then the shared indexes. Close an Issue only when its own completion or evidence-based rejection condition is met, or its unresolved question is transferred to an actual successor.

Reproduction notes: read r15 CSV; parse only canonical linked rows under the exact “Issue inventory” heading; search the 140 individual Markdown files in docs/ideas for each missing Issue’s exact GitHub URL; preserve the resulting mismatch list and do not infer semantic state from labels, titles, URLs, or row presence.
