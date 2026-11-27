# Post-hoc custody correction (C06)

The original C06 execution committed its 15 raw shards under repository-root raw/ rather than the allocation directory. Each original shard was checked against RAW_MANIFEST.json (SHA-256, byte length, row count). This commit adds byte-identical Git blobs under this allocation raw/ directory; it does not delete, move, rewrite, or reinterpret any original.

C06 remains FAIL_METHOD: its sole auditor invocation raised an exception in the mutation-control harness. This correction is custody-only, not a rerun or scientific PASS.
