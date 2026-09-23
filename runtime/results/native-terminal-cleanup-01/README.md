# Native terminal reply follows allocation cleanup

The primary assistant used the changed native harness on WSL/X11. Terminal
replies now follow artifact preservation, connection close, session close and
tracked-process polling. Each cleanup stage is attempted even if an earlier
stage fails. `cleanup.json` retains its historical process-list format; the
new report and reply expose cleanup status separately from task evaluation.

Run 1 (seed 991104) stopped before input: the assistant clicked the flat interior
of the red rectangle, which the existing visual target guard refused. The error
reply preserves this failure and reports completed cleanup with three tracked
processes terminal. The owner exec handle 1323 then returned exit 1. No replay.

Run 2 (seed 991105) used a newly viewed edge-containing point, 18 Right chords
and Save. The returned image showed x=84 instead of the goal x=86 (initial x=50,
dx=36). The cause of this short movement is unresolved. The assistant inspected
that image, issued one explicit keyboard-only Right and Save, inspected x=86,
then finished at source sequence 11. Independent SVG scoring passed. The final
reply includes three terminal tracked processes and completed cleanup; owner
exec handle 97855 separately returned exit 0. This is visible-state correction,
not automatic retry or a relabeled perfect first batch.

Eight fault/order tests plus existing exchange/review tests passed (28 total).
Coverage includes copy and connection failures, session-close failure, polling
failure, a still-running process, report persistence failure, preservation of
the original action error, and independent task failure. Publication is checked
after close/poll and report persistence. Live cleanup took approximately 64 ms
and 63 ms; this is extra work now included before reply, not a speed gain.

`completed` covers only artifact copies, close calls, and tracked direct process
return codes. It does not prove descendant termination, owner-process exit,
normal application shutdown, or input release. Those claims are not inferred
from cleanup. Release receipts remain separate. A timed-out client must resume
the same immutable request read-only. No sensor development/configuration,
helper model, Docker restart, performance or token benefit claim is involved.

Source base: b6b1ac5f1e81b45d0da12af15e7b329b44c45210. Modified live source is
retained under `source/`. The original raw run directories remain unchanged.

Run `python3 runtime/results/native-terminal-cleanup-01/audit.py` to check the
retained replies, request digests, cleanup evidence, image hashes and SVG result.
