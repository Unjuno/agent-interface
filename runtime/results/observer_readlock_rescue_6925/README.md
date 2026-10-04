# Rescue of #6925: retained observer intervention evidence

Source: `2a34f9005eb79e87a7cbc276af639154dd91a7d6`, original delivery PR #6925,
`research/observer-readlock-6526-01a0ff58-20261003`. Preserve all 75 packet files
byte-for-byte in `research/integration/observer_readlock_6526_20261003_01a0ff58`.
The complete source history is retained under annotated tag
`archive/recovered/pr6925-source-2a34f90-20261004` before retirement.
This sibling report does not change the historical frozen plan or votes.

## Fresh local validation, 2026-10-04 JST

`python -B runtime/results/observer_readlock_rescue_6925/test_archive.py -v`
passes both tests on macOS CPython 3.14.5 and bundled CPython 3.12.14.
The full local Analysis Index workflow selection passes all 43 steps
(`LOCAL_CI_SUMMARY: steps=43 failures=[]`); this is analysis/construction CI,
not a claim that every runtime/native/platform suite was executed.
Each executes the retained-data verifier in normal and optimized Python:
75 exact original Git blobs, 74 manifest entries, 16 prospective source Git
blobs/OIDs, 11 frozen source hashes, repair/raw/custody hashes, original/public
stream mappings and six historical command receipts are checked.
All 32 base64 DB/WAL/SHM capsules are decoded and hash-checked only in fresh
task-owned temporary directories. The unchanged v2 checking functions reconcile
16 recorded rows and native DB reads: 14 committed, two SQLITE_BUSY/rollback,
and two stale held WAL target snapshots. Eight copied-raw and three copied-custody
controls reproduce their exact historical rejection reasons under normal and -O.
Separate read-only main-file-only copies demonstrate four WAL omissions: those
copies show old/revision0, whereas the complete bundles show committed values.
No producer, construction deck, fresh scorer child, consumed auditor entrypoint,
or v2 historical output writer is invoked. Original packet bytes remain unchanged.

The first rescue-verifier attempt exited 1 because it omitted the separate
`validation.json` mapping of the historical missing-pytest stderr derivative.
That mapping was included explicitly; no original receipt/hash was changed.
The second attempt exited 1 because Python value equality treats True and 1 as
equal when checking corruption effectiveness. Typed canonical JSON comparison
replaced it; the original audit already uses typed JSON comparisons. Both are
rescue-verifier failures, not candidate reruns or retroactive protocol success.

Docker image inspection again returned STOP: the daemon could not read its
`python:3.12-slim` content blob (`operation not supported`). No shared VM,
daemon reset, image prune, producer repetition, or allocation was used to bypass
that condition. These archive-only checks were executed locally instead.

## Preserved boundaries and useful finding

The Windows CPython 3.11.9 / SQLite 3.45.1 finite construction is useful because
SQL read-only does not imply absence of observer intervention: a held target
read transaction prevented two DELETE-journal commits at busy_timeout0. WAL
allowed commits but held target observers still reported stale snapshots.
This is retained mechanism evidence, not a production WAL policy or GUI fix.
Initial frozen auditor exit1 stays FAIL: its no-sidecar assumption was wrong.
Sidecar custody was acquired after that failure, not at original completion.
The public exception and missing-pytest stderr are derivatives; original private
stream hashes are bound through their separate publication maps, not asserted
equal to public bytes. Initial collection exit1 and subsequent zero collection
exit5 remain unchanged. Existing #6526 HOLD_AUDIT_TIMING and other GUI allocations
are not superseded. No novelty, timing, GUI, model, game, task-effect, container,
independent content vote, or research-issue closure is claimed.
The original delivery PR can be superseded only after normal rescue integration,
main byte equality, remote tag readback, and fresh ref/dependency checks.
