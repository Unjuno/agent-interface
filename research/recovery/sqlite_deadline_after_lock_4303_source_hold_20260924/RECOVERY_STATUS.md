# Recovery status — SQLite deadline after lock wait (#4303)

This directory preserves the exact preformal source capsule recovered from
remote branch `research/sqlite-deadline-after-lock-4257-20260924`, tip
`3754e5cfa6`. The branch name/path retained the earlier #4257 label, but the
capsule and allocation identify the distinct Issue #4303 study.

## What was recovered and checked

- The original seven repository files (README, four source chunks, manifest,
  and non-executing restore script) are retained byte-for-byte under this
  recovery path. Their Git blob identities are checked against the source
  branch during recovery.
- Running only `restore.py SOURCE <new-directory>` restored the exact 10-file
  source archive; its declared size and SHA-256 matched
  `2b1538b9dcf2eddb876a303338b3ae444d3b8542edc338352fb7cf27b03e92a4`.
- The source capsule does **not** contain formal databases, process/IPC raw
  records, first control outputs, or the postformal diagnostic archive.

## Scientific disposition (unchanged)

Issue #4303 reports one consumed 36-case allocation and a raw-only audit of
2,359 checks with no row errors. The first frozen copied-evidence controls did
not establish the intended materialized-database mutation gate: three changed
DB files were rejected because WAL/SHM sidecars remained open, and later
checkpointing changed the database digests relative to the recorded mutation
receipts. A separate postformal diagnostic rejected the three semantic
mutations but does not repair or override that first control result.

Therefore the overall disposition remains
`HOLD_CONTROL_MATERIALIZATION`, not PASS. The allocation is consumed and must
not be rerun or reconstructed from the Issue summary. The reported first
outcome and diagnostic are not represented here as raw evidence. Issue #4303
remains open pending recovery of the original lossless evidence package.

This recovery is source/provenance preservation only. It makes no production,
hard-deadline, reliability-frequency, durability, task-effect, or performance
claim and changes no runtime code.
