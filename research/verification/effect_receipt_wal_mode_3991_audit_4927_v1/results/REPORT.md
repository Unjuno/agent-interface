# Partial raw integrity audit

Result: `PASS_PARTIAL_RAW_BYTE_AND_SQLITE_INTEGRITY_ONLY`.

- Files checked: 62 / 62
- Case directories: 31 / 31
- SQLite integrity checks: 62
- Decoded ZIP SHA-256: `3c57aa270e8bd3309e3b8c5aaff005b3160b501fd1391c428bace7bccee5123e`
- Effect DBs missing a `receipts` table: 31

This audit covers retained partial construction bytes only. It is not a formal experiment result and makes no WAL-vs-DELETE inference.

