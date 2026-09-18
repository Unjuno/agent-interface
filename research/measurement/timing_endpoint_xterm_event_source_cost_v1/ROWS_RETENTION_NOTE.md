# Raw 64-pair row retention

The frozen formal invocation produced the exact 64-pair row ledger before summary/audit.

- raw JSON bytes: 153,833
- raw JSON SHA-256: `ae6386be3fe95358f819952b775139d6c189a29af8eacb2aeab4da9656359810`
- gzip bytes: 18,116
- gzip SHA-256: `0b9ea733acbe8bf5b0be5e768d1c46f76e4180d39a572877c386e6f07a4d5021`
- pairs: 64

The frozen independent auditor consumed the exact raw ledger and recomputed correctness, gate counts, paired wall summaries and active-acquisition summaries. Copied-row corruption controls were rejected.

An attempted direct binary Git-object publication did not reproduce the local gzip Git blob through the text connector, so that transport artifact is not attached to the branch. The incorrect unattached blob is not referenced by any tree/commit and is not scientific evidence. The exact raw/gzip commitments above, audited summary, source freeze and corruption evidence are retained instead. No formal rerun or result regeneration occurred.
