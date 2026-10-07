# E01 result: FINDING_PARSE_FAILURE_NOT_SURFACED

Parent #59. Native producer 1, saved-only diagnostic auditor 1, retries 0.
Allocation E01-59-20261004-3CBF consumed; never replay to upgrade the result.
Freeze aa495404dc03dcd79f5d435a5bd4790fce06f16e and prospective comment
5972680010 were public before launch. Original v39 source and extracted AST
reader/wait are unchanged. No production repair made.

| Cell | Wait outcome | Observed wait | Reader at result | Child at result |
|---|---|---:|---|---|
| healthy ready | ready | 12.559247 ms | alive | alive |
| malformed `not-json` | TimeoutError | 354.941082 ms | stopped | alive |
| JSON array `[]` | TypeError | 26.076077 ms | alive | alive |

Malformed cell retains one actual reader-thread JSONDecodeError, with decoded
input doc `not-json\n`. It enqueued no event. Array cell enqueued `[ ]` as an
event value, and wait's unchecked string-key indexing raised TypeError. Healthy
cell parsed/emitted the synthetic ready object. All three owned child exit codes
0, readers retired, fatal/cleanup faults empty. No natural occurrence rate inferred.

Conclusion: under directed malformed-line input, this exact current reader/wait
subset loses the parse fault at the waiting boundary while peer remains alive.
This is a verified conditional diagnostic finding, NOT a repaired controller or
successful recovery. Array control demonstrates a separate unchecked shape path.

Native UTC 2026-10-03T19:24:38.229792476Z–19:24:38.798323507Z, exit0.
Saved auditor UTC 19:24:46.228602940Z–19:24:46.314122337Z, exit0
PASS_SAVED_DIAGNOSTIC_AUDIT, UID501. Both terminal, OOMfalse, restart0.
One immutable cached image, private VM/Engine, read-only source/root, networknone,
cpu1, memory512MiB, swap0, pids64, capdropALL. Shared physical host not exclusive.

## Evidence and limits

`raw/v39-reader-e01-3cbf-native/record/` retains nine original files, including
first typed errors, parsed event lists, peer emission receipts, source identity
and actual cgroup/UID. Auditor retains one AUDIT.json with nine native-file hashes.
Docker-cp export and host-pulled original/export copies compare byte-identically.
Source hashes after audit match frozen executable pins. Terminal inspect contains
actual commands, image, mounts, limits, timestamps. Six method tests are excluded.
Saved audit independently recomputes AST and verdict; it trusts producer's
checkpoint fields rather than independently observing threads/processes.

The .35-second timeout override is explicit; default40-second behavior was NOT
measured, and scheduling/queue-floor overshoot is not a hard-deadline guarantee.
Original nested functions are compiled into a small factory, not full v39 main.
Captured excepthook records without repairing or communicating failure to queue.
Emitted-hex sidecar plus successful write byte count is emitter provenance, not
raw stdout readback. Exception doc is actual decoded parser input evidence.
No GUI/game/model/physical release/task effect/fullcontroller adoption validated.
Runtime preflight/source inspection and transport copies are not another native
allocation. Existing T6/7103 and prior D02/D03 results preserved unchanged.

## Roadmap handoff

Verified boundary now available for an additive successor repair study: a typed
reader-failure signal should reach wait and cleanly terminate/recover the owned
session, with healthy/shape/EOF/actual-process cases and separate real-controller
adoption gates. That repair is not this experiment's result. Live task-effect and
full #59 roadmap remain open. Keep branch/VM/evidence for provenance; do not delete
while source freezes, linked worktrees or future successor dependencies exist.
