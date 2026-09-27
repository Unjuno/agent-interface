# Issue 3996: notification-stream finality, not current emptiness

Parent #3876; preserve #717 and #3938 (merged PR #3964). Unique additive
research/integration/passive_reader_finality_7f31_v1/. Base for branch:
03ac3306861c2692b796bb14e2880ba9829d8291. Full public preregistration is #3996.

H: empty/end from the exact reader does not identify producer termination.
Joined exit zero plus a producer-owned exact final extent/sequence/hash receipt
and an equally drained reader cursor can attest a complete declared stream.
A zero exit without a seal is UNKNOWN; nonzero is PRODUCER_FAILED but does not
erase received records; incomplete framing is INCOMPLETE. No task-success claim.

T: four scenarios in fixed order SEALED_COMPLETE, ZERO_EXIT_UNSEALED,
NONZERO_EXIT_SEALED, SEALED_PARTIAL, repeated three times: 12 fresh processes.
Each process uses the exact DeliveryLedger to write first and late notifications.
It waits after first-write/ready. Host reads first then empty/end, records live
poll, and only then sends finish. Producer appends the second record, writes a
seal (unless UNSEALED), and exits 7 only for NONZERO, otherwise 0. PARTIAL omits
the second record's final LF. Host joins before final continuation and tail read.
Five-second child waits; actual stdout/stderr/argv/PID/exits and before/after
bytes, all four reader responses and candidate/baseline outputs are retained.
No sleep determines order. Construction: one four-cell matrix, excluded,
plus pure candidate and raw-auditor corruption controls. Freeze source, auditor,
plan and environment on GitHub before one formal invocation. No case retries,
replacements, hidden exclusions, threshold tuning or formal reruns.

D: all 12 source/process/byte receipts reconcile; all 12 live-idle baseline
false-finality decisions vs candidate WAIT; nine complete late records delivered;
three each terminal COMPLETE / UNKNOWN / PRODUCER_FAILED / INCOMPLETE in scenario
order; partial cursor stays after first record. All reader responses remain
non-authoritative, ACK false, input false. Raw-only independent audit and at least
eight evidence corruptions must pass. Complete hypothesis mismatch is FAIL;
missing/ambiguous source/process/audit evidence is STOP/HOLD. Hypothesis PASS
never rehabilitates the unsafe empty-tail baseline.

C: owner supplies the known producer lifetime and join result, and only that
producer writes. No later writer after join, no mutation of retained log/seal.
The seal is a declared fixture protocol; existing interactive_v17 is NOT claimed
to provide it. SHA256 is integrity, not authentication. The candidate is not a
new production inbox, sensor, scheduler, ACK, or permission to replay an action.

U: no GUI/model, task outcome, useful-feedback timing, latency/token savings,
restart/epoch allocation, crash-atomic seal publication, FD sharing, retention
compaction, durability, distributed exactly-once or production qualification.
Provided Linux x86_64 / CPython3.13.5 container; Docker CLI/image identity absent.
Integer byte extents and notification counts are dimensionless counts (bytes
are octets); hashes/IDs are strings, exits are integers or unknown, clocks are
monotonic nanoseconds used only to check local order, never physical SI-time
accuracy. No statistical error probability or calibrated u_c/k is inferred.

Execution: python -S -B run.py formal NEW_DIRECTORY
Audit only: python -S -B audit.py NEW_DIRECTORY/raw.json
Independent means separate code/process by the same assistant, not a third party.

Roadmap: source verification -> excluded construction -> public hash freeze ->
one 12-case allocation -> raw-only audit/corruption -> lossless publication and
PR -> main readback and safe owned-branch cleanup. #3876/#57/global ROADMAP remain
open. The integration blocker is prematurely stopping notification draining.
