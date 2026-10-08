# Issue #4945 — matched DELETE/WAL transaction-scope experiment

## H — hypothesis

Changing only SQLite journal mode from DELETE to WAL will not change the application transaction-scope boundary. A local transaction containing both the application effect and completion receipt prevents false completion and duplicate effects across the registered process-exit cuts. Split commits expose the corresponding counterexamples; WAL does not make separate databases atomic.

## T — treatment and measurement

- One frozen local Docker image: `python:3.13.5-slim-bookworm`, image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, requested `linux/amd64` on the local OrbStack `linux/arm64` daemon; network disabled, read-only root/source, bounded CPU/memory/PIDs.
- Runtime identity must be observed in-container as CPython 3.13.5, SQLite 3.40.1, and `x86_64`; both modes use `synchronous=FULL`, WAL uses `wal_autocheckpoint=0`.
- Four protocols: `EFFECT_FIRST`, `RECEIPT_FIRST`, `ATOMIC_LOCAL` (both tables in one DB and one transaction), and `ATOMIC_EXTERNAL` (separate DBs/connections; no ATTACH).
- Five cuts: `BEFORE`, `AFTER_FIRST`, `AFTER_SECOND`, `AFTER_COMMIT`, `NORMAL`; three fresh repetitions per protocol/cut/mode: 120 rows.
- Five invalid identity/type controls per mode ×3 repetitions: 30 rows. Total 150.
- Crash cuts use child `os._exit(73)`. Preserve exact DB, rollback-journal, WAL and SHM bytes before recovery. A fresh process may perform SQLite startup recovery and read only the receipt table. It cannot inspect effects or grant authority. Retry the identical request at most once and only when receipt status is `NOT_FOUND`.
- Construction is a separately excluded invocation, not part of the 150 formal rows. If it fails, no formal invocation is authorized. After source/image/path/freeze readback, run one formal orchestrator and one independent raw-only auditor; no retries, replacements, tuning or pooling.

## D — decision

`PASS_JOURNAL_MODE_TRANSACTION_SCOPE_SCOPED` only if all 150 rows reconcile in both modes; `EFFECT_FIRST` and `ATOMIC_EXTERNAL` duplicate only at `AFTER_FIRST`, while `AFTER_SECOND` yields one effect plus receipt; `RECEIPT_FIRST` yields false completion/zero effect at `AFTER_FIRST`; `ATOMIC_LOCAL` yields exactly one effect for every cut; normal and after-commit controls are correct; all invalid controls refuse without extra effects; independent reconstruction has zero errors and rejects every frozen corruption control.

A complete contrary WAL pattern is a mode-specific FAIL. Missing rows, source/image/mode mismatch, query boundary violation, process failure, hash mismatch, or audit/control failure is a typed HOLD/STOP, not a scientific conclusion.

## C — controls

Same pinned image, SQLite build, data model, commit order, process cuts, retry rule, `synchronous=FULL`, and resource limits in both modes; journal mode is the paired treatment. Fresh DBs/operation identities per row. WAL `-shm` is diagnostic only. No models, GUI/input, network, user data, external effects, or product runtime.

## U — limits

Synthetic private SQLite and process-exit recovery only; no power/kernel loss, distributed exactly-once delivery, external service, Agent Interface runtime, GUI retry authorization, human benefit, or production claim. Transfer is limited to the two tested modes/build in this image.
