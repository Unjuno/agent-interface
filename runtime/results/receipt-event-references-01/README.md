# Same-receipt event-reference comparison

Read-only comparison of four prior actual assistant receipts. No new GUI input
or model task evaluation. Each compact projection expands exactly to its full
v1 receipt view. All full events and latest observations remain inline. The
assistant also rendered the compact Calc final receipt and its unchanged image
through the real host tool, with no external event-reference fetch.

| Retained case | Full view bytes | Reference view bytes | References |
|---|---:|---:|---:|
| XTerm, seed 991072 | 6,025 | 5,822 | 1 |
| Calc early effect, seed 991073 | 6,973 | 6,347 | 1 |
| Calc final drain, seed 991074 | 11,379 | 8,132 | 4 |
| Inkscape, seed 991076 | 7,660 | 6,934 | 2 |

Counts use identical compact UTF-8 JSON serialization, include schema/reference
metadata, and exclude image encoding. They are not model token counts. The
largest reduction is 3,247 bytes (about 28.5%); no model accuracy, response speed
or monetary benefit is established. Receipts with no duplicates can grow, so
this is opt-in. Historical receipt paths affect absolute serialized sizes.

`SUMMARY.json` pins the raw source hashes; compact views are the four named
JSON files. Source reports already live under `composed-self-use-01`,
`calc-live-review-01`, `calc-final-drain-01` and `inkscape-batch-reference-01`.
The original raw source and image are unchanged. Expansion reconstructs the
v1 presentation, not its previously omitted routine/history records.

The measurement script's first launch failed before processing any receipts
because its temporary directory was on Python's import path instead of the
repository root. Re-running with explicit `PYTHONPATH=.` produced these results;
no GUI action was issued or retried. `measure.py` retains the calculation and
has been adapted to archived inputs and a new `--out` directory, so it can run
from a fresh checkout without the original results-local directory. Replaying
changes source path lengths and therefore absolute byte counts; source hashes
and exact round trips remain the comparison identity.

Nineteen client/review/reference tests passed on Windows and WSL. They cover
exact reconstruction, unknown/near-duplicate events, escaped JSON-pointer keys,
literal reference-shaped data, invalid references and unchanged image content.
