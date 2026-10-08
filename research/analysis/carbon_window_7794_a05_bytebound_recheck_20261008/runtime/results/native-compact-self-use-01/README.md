# Optional exact native observation references

2026-09-20. An opt-in extension to the existing receipt reference helper replaces
only exact duplicates of the top-level native observation with local references.
The complete observation remains in the same response. Listed JSON-pointer paths
are references; similar-looking literal values remain literal. Distinct capture
identities, guard checks, errors, partial results and unknown fields remain.
Expansion reproduces the original native receipt. If reference metadata would
make serialized JSON larger, the original receipt is returned unchanged.

## Actual use and same-report comparison

The primary assistant used agent_exchange --native --review compact for a fresh
Calc run with seed 991085. It viewed source 1, entered 360 and 125, viewed dialog
source 7, confirmed Excel format, viewed source 12 and explicitly finished.
Two programs completed with verified release. Both the harness evaluator and a
saved-workbook reread found [360,125]. Modal-close BadWindow feedback remains
needs_review; no error was suppressed. All 12 native image/hash links passed.
Tracked processes are terminal; LibreOffice wrapper exit 255 is retained.

The same immutable replies were then reviewed in full and compact forms.
Every compact receipt expanded exactly to the full receipt and image blocks
were byte-identical. UTF-8 JSON sizes use ensure_ascii=False and compact separators:

| Stage | Text metadata full | Text metadata compact | Including base64 full | Including base64 compact |
|---|---:|---:|---:|---:|
| 1 | 7135 | 6631 | 109877 | 109373 |
| 2 | 6207 | 5704 | 84469 | 83966 |
| 3 | 557 | 557 | 570 | 570 |

Text metadata excludes the image block; comparison is of review results without
exchange timing metadata. This is about 7.1% and 8.1% less text on the two image
replies, but only 0.46% and 0.60% less with base64. Finish is unchanged. This is
modest byte reduction, not measured model-token, cost, speed or understanding
benefit. Actual primary-model usage is unavailable; helper-model calls are zero.
Keep this optional. Different values are not a held-out app or reliability sample.

## Retention and limits

run/client-*.json holds actual returned compact metadata from tool responses,
with base64 omitted; original replies/images remain in run/. Comparison JSON and
compare.py retain the post-run paired comparison without replaying input. Source
snapshots and 29 focused test results cover existing exchange/review behavior,
lossless expansion, near-duplicates, literal markers, escaped paths and small
reports. SHA256.json covers retained files except this README. The existing
response still contains distinct guard histories; these are not collapsed.
Base: 2ef9391fb50a17b38f262726b8976d6715bb9e2a.

After all GUI work and result retention, the disk filled while writing this
README. Identical archived temporary PNG copies from older runs were hash-checked
and removed, then only this isolated worktree was made sparse to omit unrelated
historical research. Git retains the omitted data; no tracked deletion is part
of this change. About 6 GB became available. This README was then rewritten.
