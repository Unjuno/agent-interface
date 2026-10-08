# Additive public-capsule recheck — 2026-10-08

This note supplements, and does not replace or edit, the original #7316 archive,
source, execution receipts, or prior reviewer record. Run
`python3 public_recheck_20261008.py` from this directory to verify the outer
manifest, all 69 gzip-capsule member hashes, the public source projections, and
the saved-only SQLite/receipt audit. The reader is copied to a disposable
directory and executed there; archived candidates, server, driver, and old
experiment entrypoints are not run.

## H / T / D / C / U

- **H:** On these already-retained native Windows SQLite receiver-restart
  cells, the saved database/process/request receipts distinguish pre-commit
  recovery from post-commit lost-reply recovery and reject contradictory copied
  outcomes.
- **T:** Re-audit the three exact saved rows using the original frozen reader,
  with one narrowly scoped public-projection exception for the failed stderr
  stream documented below.
- **D:** The frozen capsule contains 69 gzip JSON members; the outer manifest
  authenticates eight public files. The old result is not rerun. The public
  SQLite reader uses disposable copies of the captured DB/WAL/SHM snapshots.
- **C:** Frozen source Git blob/hash identities, all member bytes and hashes,
  child/outer receipts and streams, recorded HTTP request/response bodies,
  saved SQLite views, event chronology, and the original false-ack,
  double-effect, conflict-success, and unreaped-child corruption controls.
- **U:** This verifies only published, saved native Windows construction
  evidence. It does not prove private-original bytes for the projected stderr,
  current application/runtime behavior, power-loss durability, arbitrary
  schemas/writers, GUI/model/task success, or general exactly-once behavior.

## Outcome

`QUALIFIED_NATIVE_WINDOWS_RECEIVER_RESTART_CONSTRUCTION` reproduced from saved
data. Original receiver restart: exit codes 0/1 and one effect row retained.
Restart after commit/before reply: exit codes 23/0, with one effect row and
persisted `applied`, `duplicate`, `conflict`. Restart before commit: exit codes
23/0, with zero then one effect row and persisted `applied`. Four copied
contradictions are rejected. See `PUBLIC_RECHECK_RESULT_20261008.json` for the
machine-readable output.

### Explicit projection limit

The outer public archive does **not** authenticate private original stream
bytes. For `original_restart/second.stderr`, the private receipt claims 355
bytes and SHA-256
`52476de8a561ad76b10f947e6cfaf03507bcdf1b18bc9bfda0edc522db3014c2`, while
the public text projection is 286 bytes and SHA-256
`89d3dd4c89b2cbaae95bd0dc7dd4b68b6c85113ad1455c0935c8ff538ca0b8ed`. The
recheck separately compares each value against its declared domain and requires
the public projection to match its own bytes. It does not assert that the
public projection is the private stream or independently validate that private
claim. Any other mismatch still fails.

## Gate record

- Saved-only audit: **PASS**, exact command above; no actor/candidate replay.
- Container experiment: **NOT RUN**; this is a recheck of an already-completed
  Windows-native experiment, not a new experiment and not container evidence.
- Formal/current-main application gate: **HOLD**; this archive is not runtime
  adoption or an application effect.
- Original PR #7316: remains the immutable provenance source. This additive
  current-main rescue does not authorize deleting its branch or closing its PR.
- PR review/merge gate: **PENDING** independent review and GitHub-required
  checks; no direct merge or branch deletion is implied.
