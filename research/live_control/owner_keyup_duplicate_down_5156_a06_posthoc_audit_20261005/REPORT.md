# A04 retained-trace A06 posthoc reconstruction

The new read-only reader reconstructed the archived A04 candidate JSON with
zero raw errors and verified every post-run SHA-256 entry. All 11 reader tests
pass, including eight independent raw corruption cases and checks that input
tampering or a missing log is reported without changing the source evidence.

The retained candidate record contains two distinct owner-issued admissions
for the same key and intent, then one explicit `up` marked
`ambiguous_multiple_admissions`. Its nested owner KeyRelease receipt is bound
to the latest admission, the fake-Xlib calls have the expected two-press / one-
release sequence, the recorded owner interval is nested within the caller
bracket, all authority flags remain false, and both the fake keymap and verified
owner cleanup are neutral.

This reconstruction does **not** change A04's formal `STOP / consumed` status
or assign a scientific outcome. The one formal auditor invocation exited 1
before reconstruction. A05, the first posthoc reader version, also stopped
before writing a report when its evidence snapshot omitted `audit.log`; that
first result is retained in the A06 inputs and in the A05 package.

The A06 custody check confirmed a further freeze defect: the three Git blob IDs
recorded in A04's `current_main` manifest do not match the declared base commit,
and `prefreeze-audit-attempts.log` is listed but absent. Independently hashed
copies of all three dependency sources do match the declared base commit. This
narrows the provenance issue to the incorrect/missing manifest records while
leaving A04 formally STOP.

The candidate was synthetic fake-Xlib/direct-owner evidence. There was no
real-X11, physical-release, application, game, MAP01, useful-feedback, recovery,
latency, safety, or authority measurement. This work does not allocate or imply
the live #59 lane.

See [`AUDIT.json`](AUDIT.json), [`TEST_RESULTS.log`](TEST_RESULTS.log), [`OUTPUT_SHA256.json`](OUTPUT_SHA256.json), [`A05_FREEZE.json`](A05_FREEZE.json),
[`PROTOCOL.md`](PROTOCOL.md), and [`RUN.md`](RUN.md). A04 source and raw bytes
are copied into `inputs/` with their Git blob IDs and SHA-256 custody records.
The copied historical inputs remain byte-for-byte intact, including their
existing extra blank lines at EOF; the authored-file diff check is clean.
