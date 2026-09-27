# Concurrent passive-reader result commits — retained experiment

**Issue #3941; PASS_CONCURRENT_READER_COMMIT_BOUNDARY_SCOPED.** One frozen
36-case process experiment and a separate raw-only audit completed. This is a
research host-persistence fixture, not a production reader or an ACK mechanism.

## Result

| Policy | Cases | Excess retained payload entries | Cursor regressions | Stale refusals | Omitted records |
|---|---:|---:|---:|---:|---:|
| BLIND_REPLACE | 12 | 24 | 3 | 0 | 0 |
| OFFSET_MAX | 12 | 18 | 0 | 0 | 0 |
| REVISION_CAS | 12 | 0 | 0 | 9 | 0 |

Each case has six distinct original records. Excess entries measure duplicate
**local retention**, not repeated model/user consumption. The naive arms remain
rejected host policies even though the contrast hypothesis passed. No permanent
loss of producer history occurred. All input stream bytes remained unchanged;
all read receipts retained authority=none, acknowledged=false and
input_dispatched=false. No task action, GUI, model or provider call was made.

The formal run used 108 worker processes: three simultaneously resident per
case, not 108 simultaneously. All 36 first cases and their original audit were
retained; formal reruns/source changes after freeze were zero. Audit errors: 0;
semantic corruption controls rejected: 8/8. The 12 construction cases and their
8/8 controls are excluded. There were no construction or formal infrastructure
failures. The unsafe-control outcomes above are not erased by that fact.

## H / T / D / C / U

**H.** A later-completing result prepared at an old host cursor can regress the
saved cursor and retain overlapping records twice. Monotonic cursor position
alone is insufficient. Atomically comparing both the prepared revision and the
exact starting cursor before saving a response rejects stale completions.

**T.** Three policies x four schedules x three repetitions = 36 fresh cases.
Schedules: overlapping reads with smaller result committed first; larger first;
exact prepared-response replay; genuinely sequential reads. The unchanged
DeliveryLedger.prepare creates six private records. The exact main read_pending
runs in separate exec'd workers. A and B read pages of two and four records;
C makes one explicitly scheduled fresh continuation from the persisted cursor.
Pipes order operations; sleeps do not select races. Every policy stores response
and cursor in one SQLite transaction. This isolates stale-result admission,
not split-write crash recovery. Each case uses its own SQLite database.

**D.** All declared gates passed: BLIND_REPLACE regressed in all three larger-first
cases; OFFSET_MAX duplicated payloads in all nine overlap/replay cases despite
no regression; REVISION_CAS rejected all nine stale second completions without
changing retained batches or cursor and ended with the original ordered six
records exactly once in all 12 cases. Both sequential results were admitted.
The independent auditor imports none of the runner, worker or upstream reader;
it reconstructs requests, responses, prefix hashes, schedules, dispositions,
process exits, journals and final SQLite rows. Mutation copies test missing and
duplicated events, bool/int substitution, cursor changes, missing exit evidence,
changed source/payload and false authority, beyond the outer file-digest check.

**C.** Fixed trusted immutable producer lifetime, one logical host owner with
concurrent speculative reads. No production host is changed. Revision is a
local concurrency token, not permission to execute anything. A rejected response
remains raw evidence but is not a retained notification batch. This is an
extension of the reader's documented single-owner contract, not discovery of an
undocumented defect in that reader.

**U.** No crash/power-loss durability, producer-epoch recovery, hostile-producer
authentication, multi-producer ordering, random-race frequency, throughput,
useful-feedback latency, model viewing, GUI success, exactly-once delivery or
production-readiness claim. The three repeated deterministic schedules are
execution checks, not independent statistical estimates of real race incidence.
The finite study completes #3941, not parent #3876 or the full ROADMAP.

## Analytical counterexample

Let both workers start at revision 0/cursor 0. Worker B returns records 1..4 and
commits first. A later commits its already-prepared records 1..2. Blind replacement
moves the cursor 4 -> 2 and stores 1..2 twice. Choosing max(4,2) fixes the cursor,
but still stores 1..2 twice. Requiring the persisted (revision,cursor) to equal
the prepared starting pair before appending the batch rejects A. A new explicit
read from cursor 4 then retains 5..6. This is local-store reasoning only.

## Provenance and parallel work

Intake main: b2457b746a6df06f6536585dfe2ab937aff639f4. README,
docs/CURRENT_GOAL.md, ROADMAP.md, branches, open/closed Issues and PRs were read
through GitHub MCP. Exact upstream blobs are reader.py
`ea72c166c2cea511ea91031dfbb14563fe4e3245` and delivery_ledger_v2.py
`fb50be9d4d821a7836e6a0158c53a983f0f91df5`. Their bytes are copied unchanged into
upstream/ and bound by FREEZE.json. An older reader SHA in #3917 is not our input.

#3876 and merged #3883 remain the predecessor evidence. #3917 owns the live
producer boundary, #3931 response/cursor process-crash persistence, and #3933
producer-epoch binding. Those paths and allocations were not changed or rerun.
No matching concurrent-reader-commit reservation was found before #3941 creation.
Only this new research subdirectory is owned by this branch. Root README,
shared runtime, workflows, other branches and historical raw results are untouched.

The pre-formal source freeze was posted in
[issue comment 5766176053](https://github.com/Unjuno/agent-interface/issues/3941#issuecomment-5766176053).
The first result was posted in
[issue comment 5766197640](https://github.com/Unjuno/agent-interface/issues/3941#issuecomment-5766197640).
FREEZE.json SHA-256 is
`51d44b359ddd5febee427e3defc1a54b1919cc0d9753f3e6e11112bcd38c647c`.
Environment: provided Linux x86_64 execution container, CPython 3.13.5,
SQLite 3.46.1, standard library only. Docker CLI was unavailable; this is not a
Docker Desktop/OrbStack replication. Source transport used MCP, not experimental
network traffic. No package installation or credential use was needed.

## Evidence and audit-only reproduction

From this directory, with ordinary CPython and no -O/PYTHONOPTIMIZE:

```sh
python -B unpack.py /tmp/reader3941-evidence-new
python -B audit.py /tmp/reader3941-evidence-new/formal-01
```

The output directory must not exist. unpack.py verifies all part sizes/SHA-256
and Git identities, joins the 46,136-byte XZ archive, bounds decompression and
extracts 346 regular files. EVIDENCE.json identifies every part. The parts avoid
binary transport limits; they are one lossless archive, not separate allocations.
It retains raw request/response bytes, before/after snapshots, immutable streams,
SQLite databases, process argv/PID/exit/stderr, journals, run metadata and both
original audit outputs. Construction and formal directories stay separate.

The postformal transfer check compared every one of the 346 extracted files
byte-for-byte with the original. Reauditing extracted formal evidence produced
stdout byte-identical to the original audit. This verification did not rerun
any worker or experiment. unpack.py, EVIDENCE.json, RESULTS.json and this README
are postformal publication aids; none changes the frozen gate or source.

Original commands were `python -B run.py formal /mnt/data/reader3941/formal-01`
and `python -B audit.py /mnt/data/reader3941/formal-01`. Do not rerun the historical
allocation. A separately labelled replication needs a new output and allocation.

RUN.json SHA-256:
`077c2e05a32ca909cfdbb810ec79bd6e8db54a6b691a3e641c214ff8d9fac18e`.
Original audit SHA-256:
`3bd1bddc81c50aee7421721763bcefd5934cb44cd863f70b0649214b113ba270`.
Joined XZ SHA-256:
`2b6cd4171b04b6ba97a7de9ae12c8210ed8bfff1706df1f1e799b761962923f7`.

## Bounded roadmap / integration handoff

Exact source reconstruction -> excluded construction -> source freeze -> one
36-case experiment -> raw-only audit/mutation controls -> lossless publication
are complete. PR review, main readback and safe own-branch disposition are the
remaining publication steps; the Issue/PR record supplies their final status.

For an actual host integration, keep three independent obligations visible:
producer-lifetime identity (#3933), response-before-cursor retention (#3931),
and stale prepared-result admission (this study). Their separate evidence does
not establish composed correctness. Apply them to an existing real host/producer
pair under #3876; do not add an unused queue merely to combine fixtures. Retention
is still not ACK or model consumption, and no replay of uncertain action is
permitted. Actual presentation, lifecycle handling, useful-feedback measurement
and the broader same-model integrated evaluation remain open.
