# H/T/D/C/U — retained partial raw audit

Allocation: `ISSUE4927-PARTIAL-RAW-AUDIT-20260928-01`

## H — hypothesis

The 62 retained SQLite files from #4927's stopped construction are byte-identical to both the GitHub-published manifest and the lossless ZIP archive. Every database is structurally readable and passes SQLite `integrity_check`. This is an evidence-integrity claim only; it is not a scientific WAL-versus-DELETE result.

## T — bounded test

- Read exactly 31 case directories and 62 SQLite database files from the preserved `construction-01/cases/` tree.
- Independently compare the exact path set, byte length and SHA-256 of every file against `PARTIAL_RAW_MANIFEST.json`.
- Decode the published base64 ZIP in memory; verify its frozen byte length and SHA-256, exact member set, and each member's bytes against the manifest and local raw file.
- Open every SQLite database read-only and require `PRAGMA integrity_check` to return exactly `ok`; record the table inventory, including whether effect DBs have a `receipts` table.
- One local Docker invocation only. No change to the STOP allocation, no runner/construction invocation, no retry, no data writes, no network and no model/GPU/GUI.

## D — decision

`PASS_PARTIAL_RAW_BYTE_AND_SQLITE_INTEGRITY_ONLY` only if all 62 manifest rows, the entire ZIP inventory/contents, the 31-directory denominator and all 62 SQLite integrity checks reconcile. Otherwise `STOP_PARTIAL_RAW_AUDIT` with the first error. Any pass is limited to retained-artifact consistency and cannot support a WAL/DELETE inference.

## C — controls

Pin the local cached image by immutable image ID. Mount raw, manifest/archive and auditor read-only; give only a fresh output directory write access. Docker runs with `--network none`, read-only root, dropped capabilities, no-new-privileges, 0.25 CPU, 256 MiB memory, 64 PIDs and a bounded temporary filesystem. A distinct raw-only auditor imports neither experiment runner nor actor code.

## U — limits

The source allocation stopped during harness construction because a receipts table was missing in the synthetic effect DB. This audit does not repair or retry it, does not reconstruct missing cases, does not validate the WAL/DELETE protocol, and makes no scientific result claim. Historical evidence remains unchanged.

