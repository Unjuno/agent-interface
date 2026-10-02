# Recovery status for #4436

This file records a publication-integrity limitation discovered while recovering
the original branch `research/change-cue-contrast-4436-20260926`. It does not
replace or reinterpret the historical `REPORT.md`, `RESULT.json`, or `AUDIT.json`.

## Preserved claim and verification boundary

The original report claims `PASS_SOURCE_PRESERVING_CONTRAST_CUE_SCOPED` for
78,080 rows and says the original 4,756,475-byte `ROWS.csv.gz` was not published
directly. Its `RAW_MANIFEST.json` instead names
`ROWS_MEASUREMENTS.csv.xz.b64` (195,512 bytes, SHA-256
`43eb9b8e0e322b6ca5d7e0e0e13d26feccb4663f4a4103a780ac8d68b0c49abe`), but that
file is absent from the recovered branch tree. Only `raw_parts/part00.b64`
through `part05.b64` are present.

Concatenating and base64-decoding those six parts produces a truncated gzip
stream: gzip reports unexpected EOF. The decoded stream is 22,092 bytes, not the
manifest's 195,512-byte xz corpus; its SHA-256 is
`ba60bd2070730e38b81b0995fd91a8ed108d8ae87072a909579496187c394510`. The
standalone `RAW_FACTORED.json.gz.b64` also fails base64/gzip integrity checks.

Accordingly, the historical PASS and audit remain preserved as reported
artifacts, but are **not independently verified by this recovery**. No scientific
allocation was rerun, and no missing raw data was reconstructed or fabricated.
This recovery is source/report/evidence-fragment preservation only. Recovering
the complete measurement corpus or original gzip from its owner is required
before claiming a reproducible raw audit.
