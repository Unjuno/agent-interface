# Lossless evidence transport

This is a publication-only representation of the first `STOP_CLOCK_GRANULARITY` outcome. It changes no logical study byte and does not rerun any candidate, control, measurement, or auditor. The study remains 225 policy calls, 42 failed CPU aggregate guards, and zero formal post-baseline corruption controls. It does not establish a cost-characterization PASS.

The 56 original logical files total 345,660 bytes. Forty remain direct files. Sixteen repetitive JSON/JSONL data files (156,799 logical bytes) are represented by `EVIDENCE.zip.base64`: a 30,314-byte ZIP encoded as 40,421 base64 bytes including its final LF. The archive contains only five retained input JSON files, the original RAW and EVENTS records, and nine original delivered-output JSON files. No source code, executable, symlink, or directory entry is archived.

`TRANSPORT_MANIFEST.json` maps every original logical path to direct storage or an exact ZIP member, with size, SHA256 and Git blob SHA1. It binds both the decoded ZIP and encoded file. ZIP entries have fixed 1980 timestamps, regular-file mode 0644 and sorted logical paths. Compression is only data transport, not an experimental treatment.

The original `MANIFEST.json`, `FREEZE.json`, original receipts, source, construction history, and STOP report remain byte-identical. Those original manifests describe the restored logical layout, not a claim that archive-contained files are directly present in this repository checkout. The transport manifest is additive and does not replace their closure requirements.

## Data-only restoration

From this directory, run `python -S -B restore_data.py /absolute/path/to/a-new-directory` with a destination that does not exist. This helper validates the complete transport before creating the destination, rejects unexpected/duplicate/unsafe members and nonregular member types, and uses exclusive file creation. It copies direct files and decodes data; it never imports or executes study source. Treat the package as trusted retained repository material, not a general-purpose untrusted archive extractor. The destination parent must be trusted and not concurrently mutated.

After restoration, read `REPORT.md`. The complete original 56-file layout is available for read/parse/hash review. Check the original MANIFEST's 55 entries, FREEZE's 34 entries and RECEIPT output hashes against those restored bytes. Their exact SHA256 values are retained in the report and transport manifest.

Do not run `run_once.py`, the projection candidate, timing batches or the consumed controls as part of restoration or CI. This publication grants no new allocation. A future scientific attempt requires a separately approved protocol, source freeze and resource allocation.

`PUBLICATION.md` records fresh-main source scope and publication limitations. Packaging helpers/notes are outside the original scientific freeze.
