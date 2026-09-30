# Issue #5508 T15 — kill during sink transaction before commit

## H/T/D/C/U

- **H:** If the single-use receipt is already durably consumed and a sink child is SIGKILLed after its delivery row is inserted inside an open SQLite transaction but before COMMIT, reopening the sink recovers no committed effect row. Recovery must remain `UNKNOWN` (not `NOT_STARTED` and not success); the receipt stays consumed and is not replayed.
- **T:** One deterministic child-process boundary in a network-disabled pinned Python 3.12 container. The parent creates separate file-backed receipt and sink SQLite DBs, commits receipt consumption, starts one sink writer, waits for a `PRECOMMIT` barrier emitted only after the uncommitted INSERT, sends SIGKILL, and independently reopens both databases. No retry, RNG, model, GUI, network, or parameter tuning.
- **D:** PASS only if the writer emits the post-INSERT/pre-COMMIT barrier, exits `-9`, the receipt row remains `CONSUMED` with exact attempt/delivery lineage, the sink has zero delivery rows and unchanged semantic target after recovery, and an independent auditor reconstructs `UNKNOWN`. Any committed partial row, changed receipt, false success, or evidence mismatch is FAIL.
- **C:** SQLite rollback-journal recovery on one local filesystem may provide atomicity for this single DB. A different sink engine or transaction mode may behave differently; this does not bridge the receipt and effect stores atomically.
- **U:** SIGKILL is process death, not host power loss, storage/controller failure, multi-host transactions, or a real external API/GUI. The semantic target table is authored local state.

## Frozen one-case allocation

Exactly one case: consumed receipt commit -> sink `BEGIN IMMEDIATE` -> uncommitted delivery `INSERT` -> `PRECOMMIT` barrier -> SIGKILL -> independent database recovery/audit. The receipt is not replayed. No rerun or retry; infrastructure interruption is preserved as STOP and any different allocation is separately preregistered.

Base HEAD `ae727543f47e48bb1686e706b21ed5d9ba1cc31d`; OrbStack Docker Linux/ARM64 with `--network none`; pinned image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Runner/auditor/control hashes are preregistered on Issue #5508 before the single execution.

## Lineage

T12 killed before consume, after consume/before external delivery, and after a committed effect/before observation. T15 isolates the previously untested interval after the sink INSERT but before its own transaction commit; it does not repeat T12's cases.
