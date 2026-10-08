# Raw evidence bundle

`RAW_ARTIFACTS.zip.b64` is the lossless Base64 representation of
`RAW_ARTIFACTS.zip` (SHA-256
`37860792916ff5cdc0d3000af50002181b708d4fb1a56d8795a104e698849ee8`). It
contains 53 files: the one-shot `RESULT.json`, raw stdout/stderr, all per-case
inputs and supervisor outputs, independent-audit summary, and `SHA256SUMS.txt`.
The checksum file covers the other 52 files and was verified after extracting
the archive.

To reconstruct, concatenate the Base64 lines, decode to a ZIP, extract it, and
verify each path listed in `SHA256SUMS.txt`. The Base64 wrapper is used because
some Windows process artifacts contain CRLF bytes and the GitHub content path
normalizes text newlines; the archive preserves original bytes exactly.

Allocation `ISSUE3311-TERMINATION-REPORT-20260928-02` ran once: 13 tests, zero
failures/errors. A separate raw auditor accepted seven valid terminal reports
and rejected three deliberately invalid/corrupted controls. This remains a
CPU-only process/evidence-contract result, not a live desktop or efficiency
result; Issue #3311 remains open.
