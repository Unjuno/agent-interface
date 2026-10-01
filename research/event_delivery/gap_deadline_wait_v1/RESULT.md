# Result — original gap deadline versus relative inactivity wait

**Scientific disposition: PASS_WAIT_SCHEDULING_BOUNDARY_SCOPED.**
**Evidence disposition: complete for the 30-case finite local allocation.**
**Publication disposition: not published by this session; current GitHub write action unavailable.**
**Outer tool incident: retained separately after the formal process had exited0.**

## What was executed

Allocation `gap-deadline-wait-20260922-formal-01`: one formal orchestration,
30 fresh SQLite/worker cases, zero consumed-run retries/replacements or source
edits after freeze. Two wait policies, five scenarios, three repetitions.
There are 666 worker journal rows and 252 exact pipe commands. All30 worker
exits and the formal orchestrator exit are recorded as0; no recorded worker PID
remained at the post-run check. Nine unit methods pass; the separately structured
raw-only auditor accepts30/30 and rejects12/12 semantic corruptions.

The unchanged upstream `GapPolicy('ELAPSED_80MS')` is used in both arms.
Its Git blob is24221dedccca4914849c58e8edd61798ac7f9b14, verified by GitHub MCP
against main1f798cbb60b929e738c6bf8a5912470b38b45ff4. Both arms preserve
the same pending-head identity, duplicate and contiguous-admission behavior.
Only computation of the next selector wait and due-work placement differ.
`RELATIVE_WAIT` waits a fresh80 ms after every ready message.
`DEADLINE_WAIT` retains the first gap's absolute deadline and checks overdue
work before selecting again.

The producer in this experiment is the finite orchestration process. This is a
cooperative private pipe/SQLite fixture, NOT the production passive event
producer, a model, public CLI, action scheduler, or integrated inbox.

## Measurements

All entries are worker-side first-notification age from the initial same-gap
observation, in milliseconds: **median [minimum, maximum], three cases per cell**.
They are not time-to-host-presentation, model viewing, task completion or a
hard delivery deadline. Directed repeats are not population reliability samples.

| Scenario | RELATIVE_WAIT | DEADLINE_WAIT |
|---|---:|---:|
| QUIET | 80.556 [80.524, 80.632] | 80.568 [80.546, 80.627] |
| TAIL_TRAFFIC | 320.820 [320.788, 320.995] | 80.369 [80.332, 80.455] |
| BURST_THEN_QUIET | 140.757 [140.723, 140.969] | 80.900 [80.883, 81.012] |
| PREDECESSOR_BEFORE_DUE | 0 notices / 3 cases | 0 notices / 3 cases |
| BLOCKED_HANDLER | 261.462 [261.391, 261.471] | 180.966 [180.927, 181.117] |

In TAIL_TRAFFIC, E6 is offered at target offsets10 through240 ms in10 ms
increments; exact duplicates do not change the E4-missing/E5-head gap.
The relative arm postpones its notice until roughly80 ms after those messages
cease. The fixed-deadline arm services the original gap around80 ms.
Every actual inter-message gap satisfied the preregistered exposure bound.

In BURST_THEN_QUIET, E6 offers stop at60 ms. The relative arm still pays a new
full80 ms wait, while the fixed-deadline arm does not renew the gap deadline.

In PREDECESSOR_BEFORE_DUE, E4 is processed before the deadline; both arms
admit E4 then E5 once and produce no notice in all six cases. ACK remains
explicitly through E2. There is no automatic acknowledgement or resync.

In BLOCKED_HANDLER, an explicit150 ms synchronous sleep starts around30 ms.
Both arms must wait for that same thread to resume. The fixed deadline
notifies around181 ms, not80 ms. Thus the result **rejects any interpretation
that preserving an absolute deadline alone guarantees80 ms service**.
The relative arm adds a further80 ms after the blocked handler.

## Environment and timing scope

Provided Linux6.18.44 x86_64 execution container; CPython3.13.5, SQLite3.46.1,
EpollSelector, clock_gettime(CLOCK_MONOTONIC), guest CPU
AMD EPYC 9V74 80-Core Processor; five visible logical CPUs, affinity0..4.
Frequency/load are unmeasured/uncontrolled. The exact environment is retained.
Clock resolution reports1 ns, but that is not calibrated timestamp accuracy.
Kernel timeout rounding, scheduling, pipe/DB/journal operations and blocking
handlers contribute to overshoot. No calibrated combined standard uncertainty
or coverage factor is estimated. No Docker/OrbStack image/engine identity,
cross-platform replication, GUI/input, model/provider or experiment network.

The420 ms per-case command horizon is fixed. Formal orchestration, including
process startup and recording, had actual supervisory elapsed34.416805072 s.
That latter number is an execution receipt, not a per-policy performance claim.

## Complete chronology and failures

1. Main/README/CURRENT_GOAL/ROADMAP/failure-routing, recent open/closed Issues
   and PRs,118 returned branch names and targeted collision searches were read.
2. Prior #3986 was found **already merged through PR4004**, merge
   b001dcd7b69389cd4060546028b811301fd0c83a, rather than still awaiting publication.
   Its unchanged local ZIP matches the PR's SHA256.449 predecessor checksums
   passed; the original72 raw cases were re-audited without a formal rerun.
   The reconstructed audit is byte-identical to the retained audit: true.
3. Construction01 ran ten excluded cases. Nine unit methods and12 mutation
   controls passed. Before freeze, source review strengthened exact envelope
   integer/PID checks; both original and V2 construction audits are retained.
   No construction timing is pooled with formal results.
4. Local source/plan/environment freeze SHA256:
   `f894a46cfcb893d873a1dbb15f5f8145ed3b7fd39b3a12d6f889d53c197830eb`. It covers11 files. This is local prospective registration,
   NOT GitHub preregistration and NOT a premeasurement Git commit.
5. Formal runner completed30 cases and returned0; FORMAL_PROCESS.json and the
   formal END.json were durably retained in this environment.
6. The combined outer container command subsequently reported a45 s timeout.
   No audit result/exit existed at the next inspection. It is preserved in
   OUTER_TOOL_INCIDENT.json, not erased or relabeled as a scientific failure.
7. A separately invoked read-only audit of existing raw files passed, actual
   exit0, empty audit stderr. All12 corruption controls passed in a separate
   process. There was no formal rerun, source/gate edit or row replacement.
   The outer tool also surfaced a TERM-environment diagnostic; it was not
   present in the retained audit stderr.
8. Postformal source rehash matched all11 files; nine unit methods passed;
   actual worker PID absence was checked. Current main remained
   1f798cbb60b929e738c6bf8a5912470b38b45ff4 at final GitHub readback.

## Interpretation and limits

The conditional proof, all variables with Japanese definitions/SI units/domains,
unit check and counterexample assumptions are in PLAN.md. Relative inactivity
and elapsed gap age are different state machines. An absolute deadline fixes
the former confusion but does not supply event-loop availability.

The tested relative wrapper is a deliberate comparison policy, not a reported
bug in the old GapPolicy, Python selectors, SQLite or production runtime.
No same-model benefit, token reduction, physical release, model consumption,
production recommendation, arbitrary traffic bound or general starvation
probability is established. New authority is always false. Broad #3876/#57/
#2789 and ROADMAP remain open.

A same-author separately implemented auditor is not independent human review.
The audit independently reconstructs gate state, receipt hashes, input bytes,
wait-timeout calculations, accepted sequence changes, final SQLite state and
process exits. Checksums provide byte integrity, not producer authentication.

## Delivery and follow-through

This session's exposed GitHub MCP surface has48 read actions; `create` discovery
returns no action. Plugin discovery found only the already-installed GitHub
connector. No `gh`/`docker` CLI is installed and direct GitHub DNS fails. This
describes this local execution surface, NOT all workers or permanent repository
capabilities. No unsupported write workaround or new failure-only Issue is used.

The new research is addition-only under
`research/event_delivery/gap_deadline_wait_v1/`. A substantive successor and PR
draft, lossless raw evidence, exact source, freeze and verification commands
are included. The local Git carrier is explicitly not a clone/descendant of main.
No remote branch/Issue/PR was created, main changed or branch deleted by this
session. Existing merged/active branches are preserved: complete dependency
proof and an authorized delete action were not available.

ERROR CHECK:30/30 raw-case reconstruction;30 actual worker exits0;666 event rows;
252 exact commands;11/11 frozen hashes;9 unit methods;12/12 corrupted evidence
variants rejected; no consumed formal rerun. Publication and full roadmap
completion remain separate, uncompleted gates.
