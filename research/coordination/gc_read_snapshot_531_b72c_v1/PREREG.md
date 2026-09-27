# Prospective local protocol: atomic retirement / coherent read recovery

Allocation: `gc-read-snapshot-531-b72c-20260922-01`.
Registration is LOCAL before formal execution. No GitHub Issue, claim comment,
remote branch, PR or public freeze was created: the currently exposed GitHub
MCP actions are reads only; local gh and Docker are absent. This limitation is
publication status, not a scientific hypothesis or a fleet-wide blocker.

## H — changed boundary

The previous a61e allocation tested process-crash write ordering. This allocation
holds the writer to ONE atomic compaction and changes only the recovery reader's
transaction extent. Reading metadata and history in separate completed SELECTs
can combine fields from different committed states. A single read transaction
should preserve one committed snapshot. An old coherent snapshot remains old;
this does not grant current action authority or establish currentness.

This is a known transaction-composition principle tested against the exact
archived #531 model, NOT discovery of a SQLite vulnerability or an assertion
that the production runtime uses this adapter.

## T — exact finite experiment

Use full unmodified vendor531.py, Git blob
24329aaedf166b98a5babf5cfb9c61af7c6f40f0, from main
e4c2e58122aa138e421048d8e86ec18259143b9e. New private SQLite WAL stores and real
separate exec'd reader/writer processes. Writer uses BEGIN IMMEDIATE, deletes
history and advances retired_through_seq to3, then COMMIT; it never admits a
new intent and never exposes an intermediate committed state. Reader is
mode=ro, query_only ON, isolation_level=None, independent connection, no shared
cache. Every SELECT fetches all rows and explicitly closes its cursor.

Policies: AUTOCOMMIT (two individually completed SELECTs) and SNAPSHOT (BEGIN
DEFERRED before both SELECTs; COMMIT only after classification).
Component orders: META_FIRST and HISTORY_FIRST.
Writer schedules: STABLE (no compaction), BEFORE_OPEN, AFTER_BEGIN (after the
reader start acknowledgement but before first SELECT), BETWEEN_READS, and
AFTER_READS (after both components, before classification/return).
Two repetitions per cell =40 fresh cases,120 read-only classifications,80
reader/writer processes. Exact ordered cases are PLAN.json. Four immutable
serial batches of10;3-second actor response/wait limits;20-second batch child
limit. Stop on the first unexpected exception, timeout, exit, source mismatch,
missing row or evidence ambiguity. Never retry a consumed batch or pool old
or construction observations. Incomplete allocation is HOLD/STOP, not PASS.

Construction is a separate six-case block: all four BETWEEN_READS cells for
rep0 plus both SNAPSHOT AFTER_BEGIN orders for rep0. Already retained as
construction-01; never counted in formal. Offline tests and raw re-audits may
repeat, separately labelled, without repeating any experimental case.

Initial model state: apply A/1, B/2, C/3 with capacity2, leaving generation4,
history B/2+C/3 and watermark1. Atomic compaction leaves generation4, no history,
watermark3. Each reader classifies EXACT_OLD B/2 (generation2 to3), REBOUND_OLD
same B/2 with generation4 to5, and FRESH D/4 (generation4 to5). No request is
applied. NEW_INTENT_ALLOWED is the legacy read-only classifier string, not a
new input permission. Actual task/model/GUI/network calls are zero.

Retain exact RPC stdin/stdout/stderr, actual SQL traces, primitive responses,
process and supervisor exits, coherent independent SQLite backup copies of
before/after-write/final states, final original SQLite bytes and source hashes.
Backups are explicitly derived snapshot copies, not claimed raw original files.
The original final store and any remaining WAL/SHM files are also retained.
Auditor opens copies read-only and never imports runner, actor or vendor.

## D — frozen gates

PASS_GC_READ_SNAPSHOT_BOUNDARY_SCOPED requires all40 cases/120 classifications,
all80 actor exits and all4 externally observed zero batch exits, no source
changes, complete SQL/byte/process/state joins, and12 rejected evidence
corruptions. Additional exact gates:

- AUTOCOMMIT has four mixed snapshots: both component orders in BETWEEN_READS,
  two repetitions each. Both META_FIRST mixtures classify REBOUND_OLD as
  NEW_INTENT_ALLOWED and genuine FRESH as SEQUENCE_GAP (two of each).
- SNAPSHOT has zero mixtures and zero rebound proposals/fresh refusals across
  all20 cases; both policies preserve all stable/before/after controls.
- Neither policy proposes EXACT_OLD. History-containing views report original
  B as ALREADY_COMMITTED_SELF; retired views report EXPIRED_INTENT; empty-history
  watermark1 reports INVALID_TRANSITION. Do not call this unchanged-wire replay.
- AFTER_BEGIN SNAPSHOT cases see the NEW state, proving BEGIN DEFERRED is not
  the first-data-read point. BETWEEN_READS and AFTER_READS SNAPSHOT cases
  return the OLD coherent state (8 cases) despite a newer final store.
- AUTOCOMMIT has4 old coherent views at return (AFTER_READS), separately from
  its4 mixed views. Do not erase historical/currentness distinctions.
- Original and independently retained final DB states are exactly initial or
  retired according to schedule; reader total_changes is0, and SQL contains
  only the declared SELECT/BEGIN/COMMIT operations.

A complete scientific contradiction is FAIL at the exact gate; missing
provenance/denominator/process data is HOLD/STOP. The baseline remains unsuitable
for this coherent-recovery contract even if the boundary hypothesis passes.

## C / U

WAL is intentional so a writer can commit while the reader holds its snapshot.
This changes the engine concurrency mode from a61e's DELETE-journal fixture;
no cross-run timing/causal performance comparison is made. Transaction snapshot
semantics, cooperative one-writer ownership, normal filesystem operation and
honest source are assumptions. No new admissions, malicious sender, concurrent
GC writers, issuer restart, crash, power-loss, encryption/authentication,
read-to-action atomicity, real application effect, model value, latency, token
benefit, or production promotion is tested. Repetitions are finite coverage,
not a race frequency estimate. Timestamps establish same-container process
order only; calibrated combined uncertainty u_c and coverage k are unavailable,
not assigned invented values.

## Conditional derivation and variable table

| Symbol | Meaning | SI unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| g | 現在の操作世代 | 1 | model.generation | positive integer;4 throughout this study | scalar integer |
| w | 退役済み通番の上限 | 1 | model.retired_through_seq | nonnegative integer;1 or3 | scalar integer |
| h | 保持された操作receiptの順序列 | 1 | model.history | ordered by intent_seq; either B/2,C/3 or empty | finite vector of records |
| e | 次に受理可能な通番 | 1 | last history sequence plus1, otherwise watermark plus1 | positive integer | scalar integer |
| s | 提案された操作通番 | 1 | receipt.intent_seq | positive integer;2 or4 | scalar integer |

The exact model determines e = (last(h).intent_seq if h is nonempty else w)+1.
Original state gives e=4; retired state also gives e=4. A META_FIRST split read
around atomic compaction gives w=1 and empty h, hence e=2. The rebound B/2 has
s=2 and generation4 to5, so it passes the original conditions; FRESH D/4 has
s=4>e and is SEQUENCE_GAP. Exact B/2's generation2 to3 still fails generation
validation. The HISTORY_FIRST mixture retains B and C with w=3, so it is not
one of the writer's committed states, but it does not cause these two decision
errors. Thus inconsistency and a changed classification are different metrics.
A read transaction keeps the first SELECT's committed snapshot across the
second; therefore neither mixed combination occurs under the stated SQLite
isolation assumptions. BEGIN DEFERRED only disables implicit autocommit: first
data access selects the snapshot. AFTER_BEGIN is the discriminating control.

Unit check: g,w,e,s and all history sequence values are dimensionless ordinals;
only ordinals of the same semantic type are compared. Monotonic nanoseconds
are used only for RPC order/operational timeouts, never for retirement or
sequence validation. No timing distribution or physical calibration is inferred.

## Primary sources and non-overlap

SQLite isolation: https://www.sqlite.org/isolation.html
SQLite transaction / deferred behavior: https://www.sqlite.org/lang_transaction.html
#531 model is the repository contract. #3929 holds each read in one transaction
and changes WRITE publication ordering; this study changes READ extent only.
#4037 (observed at preformal recheck) concurrently admits a newer intent during
compaction; this study has NO concurrent admissions and deletes a fixed prefix.
#4026 concerns event ACK-frontier validation. #4027 concerns missing outcome
history interpretation after completed retirement. None is rerun or modified.

## Roadmap

Verify inherited bytes and current lineage -> excluded construction -> prospective
local freeze and announced hash -> four first-outcome batches -> independent
raw audit and controls -> complete additive source/evidence/report and publication
patch -> remote Issue/PR/checks/main readback when supported. The latter is NOT
claimed completed without an actual write/readback. Global ROADMAP remains open.
