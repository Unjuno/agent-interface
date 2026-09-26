# Passive-reader host persistence: process-crash boundary

Issues: #3931 (first allocation STOP), #3955 (execution-envelope successor).
Parent #3876 remains open. This is research evidence only: no production code,
queue, ACK, model-consumption, or action authority is added.

## Result and explicit acceptance boundary

**Overall successor: HOLD_EXECUTION_EXIT_UNOBSERVED.** The successor produced
all 45 raw case records and a terminal record/stdout. The external execution tool
reported timeout while the original process was still alive; that same process
later finished without any restart. The parent shell's exit file was not retained.
Its exit status is unknown. Do not infer it from worker exits or terminal stdout.

The unchanged, separately executed raw-only auditor returned exit 0,
`PASS_HOST_PERSISTENCE_BOUNDARY_SCOPED`, with zero errors and 10/10 corruption
controls rejected. This narrower semantic reconstruction does not override the
execution-envelope HOLD.

| Policy | Cases | Missing host-retained records | Duplicate host-retained records |
|---|---:|---:|---:|
| Cursor first | 15 | 18 in three split-write cases | 0 |
| Response first | 15 | 0 | 18 in three split-write cases |
| One SQLite transaction | 15 | 0 | 0 |

The unsafe cursor-first policy remains `FAIL_NOTIFICATION_RETENTION`. Missing
means absent from the host's retained responses after its resume cursor advanced;
the immutable source and off-path supervisor diagnostic response still exist.
Duplicates mean retained journal records, not observed model/user presentation.

All 90 worker exits reconcile: 36 injected `os._exit(73)` exits, 9 ordinary first
phase exits, and 45 ordinary recovery exits. These do not supply the missing
outer process status. Reader responses consistently say `authority=none`,
`acknowledged=false`, and `input_dispatched=false`.

## Preserved failure and construction

The first formal allocation, `host-crash-3931-20260922-01`, is permanently
`STOP_EXTERNAL_EXECUTION_TIMEOUT`: the 20,000 ms external tool envelope stopped
the orchestration with 25/45 complete checkpointed cases and one additional
partial store. It has no terminal record; the unchanged auditor returns exit 2,
`HOLD_AUDIT_INCOMPLETE` for missing `finished_ns`. It is not resumed, repaired,
pooled, or relabeled. All store bytes and the empty launcher output are retained.

The disjoint construction allocation has 15 cases, a successful raw-only audit,
and 10 rejected corruption controls. It is excluded from formal denominators.
There were no construction-source corrections. The successor changed only fresh
allocation/path/freeze identities and the requested outer execution envelope;
all three source files remain byte-identical. No third allocation was created.

## H / T / D / C / U

**H.** Advancing a cursor separately from retaining its response creates a crash
cut at which notifications can be skipped. Response-first avoids that omission
but may duplicate local retention on recovery. Atomic local payload/cursor
publication avoids both in this declared single-owner model.

**T.** Three persistence policies x five cuts x three repetitions, six deterministic
DeliveryLedger-format notification records per fresh case. These are fresh format
fixtures, not historical records or a live producer. The actual unchanged
`read_pending` implementation runs in exec'd host processes. Cuts are before
persistence, after first write, after second write, after commit, and normal.
Separate JSON files use atomic replace plus fsync; SQLite stages both values in
one transaction. A single declared recovery process follows each first process.
Snapshot observation uses a fresh SQLite connection and ordinary rollback
recovery, never business-level reconstruction from off-path diagnostic stdout.

**D.** Exact schedule, source, payload, persisted byte snapshots, cursors and all
worker outcomes must reconcile. Cursor-first's split cut must omit six records;
response-first's split cut must duplicate six; atomic must have neither. All ten
frozen corruptions must reject. Complete raw evidence meets these component
gates; missing outer-shell exit keeps overall acceptance at HOLD.

**C.** Provided Linux x86_64 execution container, Python 3.13.5, SQLite 3.46.1.
Docker CLI/image identity absent: NOT a Docker Desktop/OrbStack replication.
No model/provider, GUI/OS input, credential use, network in the experiment,
shared runtime mutation, or predecessor edit. Process exits are directed
fault injections, not power failure. Repetitions are deterministic controls,
not independent statistical estimates of real-world failure frequency.

**U.** No power-loss durability, fsync hardware guarantee, producer epoch identity,
concurrent host updates, distributed exactly-once delivery, ACK/model viewing,
latency/token benefit, GUI task success, or production qualification is established.
A real production producer/host and measured presentation boundary remain absent.

## Provenance and coordination

Intake/current-main readback: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Upstream reader path: `research/integration/event_inbox_reader_v1/reader.py`;
Git blob `ea72c166c2cea511ea91031dfbb14563fe4e3245`. The unmodified reader is
included here as a source snapshot. `HOST_CONTRACT.md` at the upstream path,
blob `89eda6a5029781c09cfafe229b7831f8be2670d9`, already predicts the ordering
boundary. This experiment supplies process/filesystem observations, not a new
undocumented upstream defect or a new theorem about SQLite.

Startup inspected README, CURRENT_GOAL, ROADMAP, branches, recent open/closed
Issues and PRs, closed #771, and #2197/#3876/#493 histories. It was not an exhaustive
repository census. An initial targeted search rate-limit was retained in #3931;
the later successful search found disjoint parallel scopes: #3933 producer
epochs, #3938 generation-path publication, #3941 concurrent read commits, and
#3917 live producer reading. They explicitly exclude this persistence allocation.
No other branch/path or global README/ROADMAP was changed.

## Reproduce the retained audit (no new experiment)

The four `evidence.tar.xz.partNN` pieces concatenate to one XZ archive containing both allocation directories, source snapshots,
freezes, all raw JSON and native store files, construction, first STOP, second
HOLD, audit outputs and exit observations. The verifier checks and joins all four parts. Binary transport avoids JSON/whitespace
normalization of original evidence. `MANIFEST.json` binds archive and critical
files. The source `study.py` and `audit.py` are also visible for review.

From this directory, use an empty output path:

```sh
python verify_bundle.py --out /tmp/host-crash-3931-evidence
cd /tmp/host-crash-3931-evidence/allocation02
python audit.py formal-02/raw.json --controls
cd ../allocation01
python audit.py formal-01/raw.json --controls
```

Expected: successor raw audit exits 0 with the scoped component PASS; first
allocation audit exits 2 with `HOLD_AUDIT_INCOMPLETE`. The latter failure is correct
and must not be repaired. These are read-only audits, not formal reruns. Never run
`study.py formal` using either consumed identity; a new experiment requires a
separately preregistered allocation and terminal-status retention plan.

## Bounded roadmap and handoff

Completed: source reconstruction; excluded construction; preformal GitHub hash
freezes; one first allocation with retained STOP; one successor with 45 complete
raw cases and retained outer-exit HOLD; separate raw-only audit/corruption checks;
additive evidence packaging. GitHub PR/main status belongs to the PR and issue
history, not to this frozen experimental result.

Integration decision: preserve response-before-cursor ordering; treat atomic
local retention as a scoped candidate only. Do not silently adopt this fixture
as a production queue. Further adoption needs an existing real host endpoint,
producer lifetime identity, concurrent update semantics, explicit presentation/
ACK boundaries, and end-to-end validation. The missing outer exit cannot be
reconstructed from existing bytes; it remains unknown, not a reason to alter
old data. #3876 and the overall ROADMAP remain open.
