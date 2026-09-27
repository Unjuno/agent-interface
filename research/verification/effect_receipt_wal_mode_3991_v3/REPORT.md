# Allocation-03 report — construction-audit STOP

## Disposition

`STOP_HARNESS_INDEPENDENT_AUDIT` — construction runner PASS; independent
construction audit FAIL; formal invocation count 0. This is an auditor/evidence
access failure, not a scientific DELETE-vs-WAL result. Allocation-03 is
consumed under its preregistered STOP rule. No repair, retry, replacement,
pooling, or formal run is authorized for this allocation.

## Frozen construction outcome

The pinned OrbStack container (`python:3.13.5-slim-bookworm`, image ID
`sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`,
linux/amd64) observed CPython 3.13.5, SQLite 3.40.1, and x86_64. It ran with
network disabled, read-only root/source, 1 CPU, 1 GiB memory, and 32 PIDs. All
four construction unit tests passed. The runner emitted all 50 preregistered
construction rows and exited 0. `construction.jsonl` is 208,159 bytes with
SHA-256 `f72c6d0bde34e676e52c3af6881e6a204ec23198fe9343b6b9f7d84123337e51`.

## Independent audit outcome

The separate pinned-container audit read all 50 rows and rejected all 8 frozen
corruption controls, but exited 2 with `FAIL_AUDIT` and 25 errors. Every error
is `independent_database_read:OperationalError`, covering the 25 WAL-mode
rows; there are no audit errors for the 25 DELETE-mode rows. The independent
auditor could not read the final WAL-mode databases from its read-only-mounted
evidence directory. The frozen auditor records the exception type but not its
message, so the precise SQLite/filesystem failure detail is unavailable. Do
not infer whether journal-mode semantics caused the discrepancy: this is a
failed audit gate, not a WAL behavior finding.

Retained evidence:

- `results/construction/`: environment, exact host Docker invocation receipt,
  stdout/stderr bytes, 50 JSONL rows, and all per-case DB/journal/WAL snapshots.
- `results/construction_audit/`: independent `AUDIT.json`, exact host Docker
  invocation receipt, and stdout/stderr bytes.
- `FREEZE.json` and `SOURCE_MANIFEST.json`: source and allocation identity.

There is no `results/formal/` directory and no formal output. The user's
requested final local CI check is `python research/check_workspace_index.py`;
the run before adding this report passed, and it must be repeated after this
report is added before packaging the STOP evidence.

## Scope

No formal rows were executed. Construction cases are excluded and cannot
support a DELETE/WAL comparison. No production, durability-under-power-loss,
distributed exactly-once, or Agent Interface runtime conclusion follows.
