# Pre-registration plan — Issue #4945

## Lineage

This is allocation `effect-receipt-wal-vs-delete-3991-20260928-03`, a fresh
successor to the preserved `STOP_HARNESS_CONSTRUCTION` outcomes in #4927 and
allocation `...-02`, isolated from `...-02` by a distinct branch and path. The
#4927 allocation produced
31 partial case directories, failed because its `ATOMIC_LOCAL` fixture omitted
the `receipts` table from the local effect database, and started zero formal
cases. Preserve that STOP, its branch and path, and #3991 unchanged. This
allocation has new source, new case identities, and no pooled rows.

## H — hypothesis

Changing only SQLite journal mode (DELETE vs WAL) does not change the
application transaction-scope boundary. One local transaction containing both
the effect and completion receipt avoids false completion and duplicate effect
at registered process-exit cuts; split commits expose the directed
counterexamples. WAL does not make separate databases/connections atomic.

## T — finite local allocation

Base main: `3b9984e33286ffa7cae8f48636131c272ebaf27d` at pre-registration.
Container: cached image
`sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`,
linux/amd64, CPython 3.13.5 / SQLite 3.40.1. Run with `--pull=never`,
`--network=none`, `--read-only`, 1 CPU, 1 GiB, 32 PIDs, read-only `/src`, and
fresh writable `/out`. Both modes use `synchronous=FULL`; WAL additionally
uses `wal_autocheckpoint=0`.

Four protocols:

- `EFFECT_FIRST`: commit effect, then separately commit receipt.
- `RECEIPT_FIRST`: commit receipt, then separately commit effect.
- `ATOMIC_LOCAL`: one database transaction contains both records.
- `ATOMIC_EXTERNAL`: effect and receipt commit to separate databases; no
  `ATTACH` or coordinated multi-file transaction.

Five cuts: `BEFORE` writes; `AFTER_FIRST` immediately after the first
independent commit (or first uncommitted write for `ATOMIC_LOCAL`);
`AFTER_SECOND` after both independent commits (or both local writes are staged
but before commit); `AFTER_COMMIT`; and `NORMAL`. Crash cuts use actual
`os._exit(73)`. After actor exit, exact database/journal/WAL bytes are copied
before normal SQLite recovery. A recovery-only process opens/closes each DB;
it performs no application operation. A separate read-only receipt query has
an SQLite authorizer denying writes and reads of the effects table. It is the
only source for status. Exactly one same-request retry is permitted iff that
query reports `NOT_FOUND`.

Formal denominator: 2 modes × 4 protocols × 5 cuts × 3 fresh repetitions =
120 rows, plus 5 invalid identity/type controls × 3 repetitions × 2 modes =
30 rows, total 150. Invalid controls cover altered content under an existing
operation identity, wrong session, wrong resource, wrong epoch, and
boolean-as-integer delta. Every control must refuse and add zero effects.

One excluded construction invocation runs the same 40 protocol/mode/cut cells
at one repetition plus five invalid controls per mode (50 rows), checks schema
for every declared database, real process exit/cut ordering, expected recovery,
artifact retention, and the independent auditor's corruption controls. It is
not formal evidence. Any construction failure is a retained STOP; no formal
invocation follows.

The allocation-02 construction STOP identified two prospective auditor defects:
its expected denominator did not vary with construction vs formal, and its
`AFTER_SECOND` retry expectation ignored the protocol. This auditor derives its
denominator from the frozen phase and uses the explicit state/status matrix:
split protocols at `AFTER_SECOND` have both commits and do not retry, whereas
`ATOMIC_LOCAL` has uncommitted writes, rolls back, and retries only after
receipt-only `NOT_FOUND`.

Before execution, post this immutable plan, source/freeze hashes, exact image,
and paths to #4945 for readback. Keep code and evidence local through
construction, formal, and audits; after results and local CI are complete,
commit and push the source plus raw and audited evidence together. Formal is
one orchestration and one separate raw-only audit. No retry, replacement,
pooling, seed substitution, or post-result tuning.

Host worktree: `/Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/`.
Branch: `research/effect-receipt-wal-3991-20260928-v3`.
Source mount: `/Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/`.
Construction evidence: `results/construction/`; construction audit:
`results/construction_audit/`; formal evidence: `results/formal/`; formal audit:
`results/formal_audit/`, all relative to the source mount. The host-only
`launch.py` captures Docker argv, PID, exit, stdout/stderr bytes and hashes for
each stage. Exact host commands:

```text
python3 /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/launch.py construction /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/results/construction
python3 /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/launch.py audit-construction /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/results/construction /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/results/construction_audit
python3 /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/launch.py formal /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/results/formal
python3 /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/launch.py audit-formal /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/results/formal /Users/taka/Documents/Codex/2026-09-28/agent-interface-wal-v2/research/verification/effect_receipt_wal_mode_3991_v3/results/formal_audit
```

## D — decisions

`PASS_JOURNAL_MODE_TRANSACTION_SCOPE_SCOPED` requires exact reconciliation of
all 150 rows in both modes; `EFFECT_FIRST` and `ATOMIC_EXTERNAL` expose an
unrecorded effect followed by a duplicate only at `AFTER_FIRST`; at
`AFTER_SECOND` both commits already completed and final state is one effect
plus one receipt without retry; `RECEIPT_FIRST` exposes false `COMPLETED` with
zero effect only at `AFTER_FIRST`; `ATOMIC_LOCAL` ends with exactly one effect
and receipt for every cut; invalid controls refuse with zero added effect;
and an independent raw-only reconstruction reports zero errors and rejects
all eight frozen corruption controls.

A complete contrary WAL pattern is a mode-specific FAIL/contradiction.
Missing rows, process/image/mode/source mismatch, query access to effects,
hash mismatch, or audit/corruption failure is typed HOLD/STOP, not a scientific
conclusion. Preserve raw files and every process exit.

## C — controls

Same pinned image/SQLite build, schema, transaction ordering, crash cuts,
recovery and retry rules, synchronous mode, matrix, and resource settings;
journal mode is the paired treatment. Databases and identities are fresh per
case. WAL `-shm` bytes are diagnostic, not durable application evidence. No
model/provider, GUI/input, network, user data, external effect, or runtime
change.

## U — limits

This is a synthetic private SQLite application and process-exit experiment,
not power/kernel-loss durability, distributed exactly-once delivery, external
service behavior, Agent Interface runtime integration, GUI retry authorization,
human benefit, or production qualification. Transfer is limited to these two
SQLite journal modes/builds in this local image.
