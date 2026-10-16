# Line-aware saved-evidence pages v2

Actual v1 use split the coordinate 641 across pages as 64 / 1. The opt-in v2
reader prefers the last complete LF-terminated line fitting the full JSON wire
limit. If a single line cannot fit, it falls back to a UTF-8 character boundary.
`starts_mid_line` and `ends_mid_line` make that fallback explicit. Reconstruction
checks both markers against exact reconstructed bytes, in addition to contiguity,
source identity and end markers. A complete line is not a complete semantic event.

The frozen v1 remains unchanged. V2 keeps the 8 MiB input cap, 1024–65536 wire-byte
limit, digest-required resume, exact-byte reconstruction, and no runtime/input
authority. CRLF bytes are preserved; LF is the recognized delimiter. A bare CR is
ordinary content. Fragments cannot be treated as runtime receipts or task approval.

On the actual 17,624-byte overflow report:

| Wire limit | v1 pages / total bytes | v2 pages / total bytes | v2 partial-line endings |
| --- | ---: | ---: | ---: |
| 1024 | 28 / 28,244 | 31 / 30,650 | 0 |
| 4096 | 6 / 21,056 | 6 / 21,332 | 0 |

This trades a small amount of metadata/space for line readability. It is not token
compression; at small limits it increases page count. Neither source byte size nor
wire size measures actual model tokens. Exactness and wire bounds are verified,
not model receipt, live task quality or faster judgment.

The probe covers six sources at two limits: the historical report, oversized
Unicode/escape-heavy lines, CRLF, empty input, no trailing newline, and many blank
lines. Every case reconstructs exactly within the wire cap. Ten negative cases
reject missing/duplicate/reordered pages and altered content/identity/cursor/end/
partial-line markers. Long Unicode lines exercise explicit partial-line fallback.

Run `python3 research/live_control/probe_report_pages_v2.py`; evidence is
`results/report-pages-v2-01/report.json`. CLI usage matches v1, substituting
`report_pages_v2.py`. Do not mix v1 and v2 page streams.

Next test end-to-end integration on a fresh private task with explicit presentation
coverage and image inspection. Do not continue accumulating offline formatting
variants without observed task-level benefit. The unresolved black-image path and
missing authoritative model receipts/tokens remain separate limitations.
