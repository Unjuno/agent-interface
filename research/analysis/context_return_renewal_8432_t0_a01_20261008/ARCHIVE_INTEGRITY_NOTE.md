# Post-publication raw-byte integrity note

This addendum records a discrepancy found while preparing the retained A01 package for merge. It does not alter or replace the original result, manifest, run receipt, or raw file.

- `MANIFEST.json`, `REPORT.md`, and `RUN_RECEIPT.json` declare the one-shot `RAW.json` digest as `8e448a60072da2e53822da417d32446c4910a262b3da56c92c55a2af296eaa2f`.
- The exact committed Git blob at reviewed head `52fd2f53c1eee22e40baa5db6373a0ab497a4c08` hashes to `f017bb5c74ae748eaa4e029b40c989123a24e2cd249e9f9551d63ef10c8386e3`.
- Simple LF/CRLF and terminal-newline variants did not reconcile the digests.

No candidate or auditor was rerun, and no original frozen or result artifact was edited. The raw bytes currently in Git are preserved exactly as published; their identity with the one-shot candidate output is **unverified**. The recorded auditor failure and 9-versus-12 method-gate inconsistency remain preserved as reported, but this package must not be treated as independently byte-verified experimental evidence or as a scientific result.

A future provenance recovery must be additive: recover an independently retained original output or a trustworthy publication receipt, preserve the current Git blob and these hashes, and explain the discrepancy without overwriting either version. Do not rerun the one-shot allocation to replace the missing provenance.
