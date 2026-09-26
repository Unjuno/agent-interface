# Shared descriptor position is not an independent read cursor

## Outcome and exact scope

Issue #3995: **PASS_SHARED_OFFSET_BOUNDARY_SCOPED**. One fresh54-case formal
allocation,108 distinct exec'd workers, all worker exits0; supervisor exit0 directly
recorded. Separate frozen raw-only audit: exit0/errors0;10/10 corruptions rejected.
Eight offline test methods passed. No formal retry, source/gate change or pooling.

Issue #3984 remains **STOP_COMMAND_EXECUTABLE_NOT_FOUND**: an erroneous publicly
transcribed /usr/local/bin/python returned shell127 before any Python/formal case.
The local freeze had the correct /opt/pyvenv/bin/python. The correction was registered
as #3995 with a new allocation/path, identical scientific source and new hash freeze.
The first STOP and original freeze remain unchanged; no success is inferred for it.

| Policy | Cases | Responses delivered | Refusals | Incomplete acquisitions exposed |
|---|---:|---:|---:|---:|
| UNCHECKED_DUP |18|36|0|12|
| CHECKED_DUP |18|24|12|0|
| PREAD |18|36|0|0|

Each case has two readers. The unchecked12 failures are6 empty snapshots in BOTH_RESET
and6 one-record snapshots in INTERRUPTED_CHUNK, across named/unlinked states.
The exact existing reader correctly reports the end of those shorter snapshots; the
adapter must not promote that into proof of complete source acquisition. The checked
control refuses those12 captures. PREAD returns all6 notifications in all36 responses.
UNCHECKED_DUP therefore remains **FAIL_ACQUISITION_COMPLETENESS**.

## H/T/D/C/U

H: retained file identity and per-reader position are distinct requirements.
T: 3 policies x3 barrier schedules x2 name states x3 repetitions, exact current-main
reader and DeliveryLedger v2; private immutable regular file; real process/FD sharing.
D: complete54-case/108-exit/source/offset/bytes/cursor/cleanup reconciliation,12 expected
unchecked failures,12 checked refusals,36/36 PREAD complete responses,10 controls.
C: pread isolates offsets but does not make a changing inode immutable; explicit EOF
and trusted producer lifetime remain assumptions. Unlink is after both ready replies.
U: finite directed cases, not a race-frequency or throughput/latency estimate. No GUI,
model/provider, input, ACK/consumption, producer restart, hostile authenticity,
concurrent append/in-place write, cross-platform or production-result claim.

## Mechanism and analytic-first prediction

The stream is426 bytes (six71-byte records). After both duplicate descriptors seek
to0, reader A consumes426 bytes. Reader B then reads from the shared EOF and gets0.
In the interrupted schedule A first takes71 bytes; B resets/consumes426; A's remaining
read returns0, leaving only the first71 bytes. These effects follow the shared open
file description, not an error in the source corpus or the upstream reader.

The positional candidate reads at its own accumulated-byte offset. Thus A and B each
request their own initial offset0; A's second segment, when present, starts at71.
Shared SEEK_CUR may change due to reset commands but cannot redirect those explicit
position reads. In this immutable fixed-EOF allocation they reconstruct the whole
original file, including when its directory entry has been removed.

The numerical byte counts above are verified from the actual corpus; timestamps only
order barrier operations. PLAN.md includes the complete variable/unit table and byte
dimension check. There is no conversion of bytes to tokens or timing to task benefit.
Primary implementation reference: Python3.13 os.pread documentation; it states that
explicit-position reads leave the shared file offset unchanged.
https://docs.python.org/3.13/library/os.html#os.pread

## Provenance and preservation

Base main b2457b746a6df06f6536585dfe2ab937aff639f4.
Corrected public hash/command freeze: #3995 comment5766604317.
First result: #3995 comment5766616093.
Successor freeze SHA256: 4db6d275147699503d1f595b2885eae0f9d8277166391f823e6dbfe487c6f961.
Successor audit SHA256: 7f10d3347829df79994c98f9273568da759884fc753d7d5637a7ee9ea9e19075.
Raw-set SHA256: ecc69fbb891c275d62a779531327ff3998d5461fe413f27d43bf03b9004e60d4.
Raw-set digest is SHA256 of sorted compact JSON of AUDIT.json.raw_sha256.

The supplied Linux x86_64/CPython3.13.5 execution container has no Docker CLI or image
identity; no Docker/OrbStack or network-namespace equivalence is claimed. Study code
makes no network calls. Explicit -I -S -B workers use256MiB address-space/5CPU-second
limits. Actual CPU details/clock assumptions are in ENVIRONMENT.json; frequency/load
are unpinned and no performance result is reported.

Original18 construction cases and8 tests are distinct from formal54. Retained source,
all snapshots/source bytes, framed commands/replies, child exits, offsets/stat fields,
original STOP and both freezes are packaged losslessly. The independent auditor is
a separate implementation/process by the same author, not an external review.
SUPERVISOR_CHECK.json separately checks actual parent exit/command/source/time order;
this postformal read-only check does not modify the frozen auditor or original data.

## Integration handoff and related fields

This constrains acquisition for the #3876 retained-event path; it is not a production
queue. A host that shares retained handles needs positional reads or explicitly
serialized seek/read; only positional reads were tested here. Preserve record
identity, complete acquisition and no-authority response semantics separately.

Operating systems: distinguish file descriptor lifetime from shared open-description
position. Database/event processing: do not treat an empty acquired buffer as proven
stream completion. Agent-interface design: trustworthy acquisition precedes event
interpretation, and neither establishes model consumption or permission to act.

No shared runtime, workflow, root README, previous result or other branch is edited.
Publish this evidence and the original STOP through an additive PR, inspect current
checks/reviews and read back main. Keep #3876 and global ROADMAP open.
