# Formal failure record

The candidate program completed once, but the independent auditor exited 1 before parsing the candidate rows because its input loader treated plain `.jsonl` as gzip. Disposition: `STOP_AUDIT_INPUT_FORMAT` / `NOT_EVALUATED`; there is no scientific result. Exact commands, timestamps, raw bytes, hashes and integrity gates are in [`RUN.json`](RUN.json), with complete context in [`STOP.md`](STOP.md). No retry or patched replay was performed.
