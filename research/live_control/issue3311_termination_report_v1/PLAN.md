# Issue #3311 incomplete-run reporting contract

Status: one bounded host-only contract test; this is not a #3311 formal allocation.

## H — hypothesis

The frozen integrated-efficiency evaluator rejects an arm with fewer than six
task rows, while the existing runner writes its final trace/report only after
all arms return. A separate process supervisor can preserve the interrupted
run's existing bytes and emit an independently auditable `HOLD` termination
record, without mislabeling incomplete evidence as `REJECT`. A source mismatch
or child-launch failure before execution is `STOP`.

## T — bounded diagnostic

- Intake main: `e8b4071931df81b3408a5d0a91c7607c6323c9c9`.
- Frozen current evaluator blob: `e8e5ee9e3abb66cb7673ac90ec9074820a16cac9`.
- Frozen current runner blob: `7551eaf8112a48a893b204db9fae9105c1c10899`.
- Preserve both frozen files and all existing result directories byte-for-byte.
- Exercise the exact evaluator on synthetic complete and one-row-short traces;
  exercise the new supervisor using disposable child processes that exit
  nonzero, omit output, mismatch source pins, or produce a valid audited pair.
- Independently audit the terminal report from disk, recomputing every listed
  artifact size and SHA-256. Include tampered-hash, path traversal, and
  disposition-confusion mutations.
- Run the finite unittest suite once on this PC (CPython 3.11.9). Do not start
  Docker/OrbStack: no shared-slot ownership was transferred to this lane.
- No provider/model call, GUI, task input, GPU, network, or formal allocation.

## D — decision

`PASS_TERMINATION_HOLD_CONTRACT_SCOPED` iff the current evaluator accepts the
complete synthetic control and refuses the six-row omission; the supervisor
records child failure/missing output as HOLD, pre-run source/launch failure as
STOP, never infers REJECT, preserves existing report bytes, and an independent
raw-file auditor accepts the valid report while rejecting every declared
corruption. Any false acceptance or disposition confusion is
`FAIL_TERMINATION_CONTRACT`; source/test/provenance/integrity failure is
`STOP_CONSTRUCTION_OR_PROVENANCE`.

This does not establish that the historical runner used a supervisor or that a
future integrated allocation is complete. It is narrowly the missing
termination-record contract required by #3311's unfinished/terminated-run and
HOLD requirements.

## C — controls

One fixed source snapshot; deterministic synthetic inputs; separate subprocess
boundaries; complete RETAIN/HOLD/REJECT and incomplete/failure controls; the
independent auditor does not import the candidate supervisor. No historical evidence,
runtime behavior, model usage, or task outcome is changed.

## U — limits / stop conditions

The supervisor cannot persist a report if it, the OS, or the machine is
forcibly terminated before the write. That boundary remains explicitly
uncovered. This does not repair or replace frozen runner v1; any future use must
be integrated into an additive re-frozen runner/allocation. No efficiency,
correctness, human-tempo, safety, or product claim follows.
