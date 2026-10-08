# Resumable saved-evidence pages v1

`report_pages_v1.py` is an opt-in offline reader. It bounds each emitted UTF-8
JSON line, including envelope and newline, to a caller-selected 1024–65536 bytes
(default 4096). It preserves the exact source bytes, including whitespace, with
UTF-8 character boundaries. It reads at most 8 MiB + 1 and rejects oversized or
invalid UTF-8 input. It never calls the runtime or sends input.

Every page names source SHA-256, total bytes, starting and next byte offsets,
fragment text, and a source-end flag. Nonzero offsets require the expected digest.
The end flag means only that this slice reaches the file end: it does not prove
prior-page coverage, model receipt, task completion, or input approval. Fragments
can split JSON values and must not be interpreted as complete runtime receipts.
Keep the original report and use `reconstruct(pages)` to verify full contiguous
coverage and source digest. Missing, reordered, duplicate or altered pages fail.

Example from the repository root:

```text
python3 research/live_control/report_pages_v1.py research/live_control/results/recovery-pair3-01/B/build/result.json --limit 4096
```

Resume with the returned `next` as `--after` and `sha256` as `--sha256`. A fresh
call rechecks the source digest. A changed source must start a new evidence stream.
This is ordinary hash-based identity, not signed provenance or durable receipts.

The offline probe used the actual pair 3 B overflowing result (17,624 bytes):
28 pages at a 1024-byte limit, each within the complete wire bound, with exact
reconstruction. Unicode/emoji/escape-heavy text and empty input also round-trip.
Thirteen negative controls cover missing/reordered/duplicate pages, corrupted
content/identity/end/cursor, absent digest, invalid UTF-8 cursor boundaries and
invalid limits. Reproduce with `python3 research/live_control/probe_report_pages_v1.py`.
Evidence is `results/report-pages-01/report.json`.

This is not compression: envelopes and escaping add bytes, and smaller pages add
calls. A byte bound is not a token or remaining-context bound. The entire process
does not have a hard latency guarantee. Full-source decoding/hashing is repeated
per page within the input cap. No fresh live self-use or model receipt validation
has run. The black-image presentation path is unaffected.

Next validate actual resumed inspection of the saved overflow case, including a
lost page response without resending task input. Then define a fresh allocation
before integrating this display contract into live comparisons. Preserve v1 measured
source bytes and all previous registered study results.
