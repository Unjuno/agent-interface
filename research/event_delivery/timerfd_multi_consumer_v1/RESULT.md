# Timerfd multi-consumer ownership — first formal result

**PASS_TIMERFD_OWNERSHIP_BOUNDARY_SCOPED**. This is a local Linux API/notification-ownership validation,
not an integrated Agent Interface desktop result, a new OS discovery or a
production bug allegation. No runtime default or executable shared source changed.

## Lineage, chronology and scope

Originating Issue #4001 explicitly excludes descriptor duplication and multiple
readers from its completed single-owner accounting experiment. This allocation
changes that ownership factor. Closed #3986 and #4031 and previous conversation
`timer_episode_binding_v1` are preserved, never rerun. The latter is now tracked
by open #4044; the older wait experiment is merged through PR #4035 at
`e4c2e58122aa138e421048d8e86ec18259143b9e`. These remote publications were observed,
not performed in this session. A targeted PR search for #4044 found no result;
that is bounded search coverage, not proof that no unpublished PR work exists.

Current-main intake and final readback both resolve to
`e4c2e58122aa138e421048d8e86ec18259143b9e`. README, CURRENT_GOAL, ROADMAP,
INTEGRATION_PLAN, recent open/closed Issues, open PRs and two branch pages
(100 + 25 returned names; not an atomic snapshot) were read via GitHub MCP.
The public CLI attempt module was also inspected: this test does not invoke it.
No fake facade is represented as a production end-to-end route.

Source/gates were frozen locally at 2026-09-21T22:19:06.359096+00:00. GitHub write operations
were not exposed by this session's connector; this is **not public preregistration**.
Only this new namespace is owned locally. The exact path and branch-keyword
searches found no matching claimant before formal execution; unpushed work is
unknown. No other worker/branch/process was changed.

## H / T / D / C / U

- **H:** aliases of one timerfd do not supply independent notification consumption
  or rearm/disarm state, even across distinct exec'd workers. Distinct timer
  objects isolate those states. Closing one alias differs from cancelling the timer.
- **T:** two modes, five schedules, two repetitions: **20 fresh cases and 40 actors**.
  Two predefined ten-case batches. One initial one-shot deadline, 100 ms ahead;
  A-only rearm is 3 s ahead and B is checked before it. These are fixture intervals,
  not latency goals. Separate construction contains ten excluded cases.
- **D:** all exact count/readiness/rearm/disarm/close outcomes, byte/FD/process
  identities, unchanged sources and independent raw-only audit must agree. All do.
- **C:** reliable single-container CLOCK_MONOTONIC, nonblocking descriptors, no
  unrecorded timer mutator/reader, no injected ticks, and the registered one-shot
  schedules. Neither mode is claimed to implement a broadcast delivery protocol.
- **U:** no model/GUI/task input, actual observation acquisition, token savings,
  performance advantage, natural race frequency, hard deadlines, suspend/restart,
  non-Linux, arbitrary concurrent mutation, or production admission is established.

The full variable table, SI-unit check, complete conditional argument, fixed
schedule, stop rules and implementation assumptions are in PLAN.md.

## Observed formal outcomes

Every table cell is observed in both repetitions. Read count has SI unit 1;
EAGAIN means no unread expiration, not a timeout or failed worker process.
A and B are two distinct actor processes, not two timer samples.

| Schedule | Shared aliases (`SHARED_DUP`) | Distinct objects (`INDEPENDENT_CREATE`) |
|---|---|---|
| A reads first | A reads 1; B gets EAGAIN after both had reported ready | A reads 1; B reads 1 |
| B reads first | B reads 1; A gets EAGAIN after both had reported ready | B reads 1; A reads 1 |
| A rearms after both ready | B's old unread count disappears; its timer is now in the future | B still reads its old count 1 |
| A disarms after both ready | B's old unread count disappears | B still reads count 1 |
| A closes its handle | B still reads count 1 | B still reads count 1 |

Shared mode: 10 cases, 6 successful native reads and 8 EAGAIN reads.
Independent mode: 10 cases, 14 successful native reads and 0 EAGAIN reads.
Four shared-mode cases specifically retain *both initially readable* followed
by the second reader's EAGAIN. No data is fabricated for those unavailable reads.
Native fdinfo snapshots independently show the pending-count and remaining-time
changes. Anonymous-inode equality was not used as proof of timer identity.

The independent mode has separate timer objects; its two native counts are not
two independently observed application events. Shared aliases are not intrinsically
incorrect: they can be intentional shared consumption. They fail only the proposed
assumption that giving each worker a handle grants independent timeout ownership.

## Interpretation / concrete integration constraint

A file descriptor is a reference to a kernel timer, not a per-subscriber mailbox.
Readiness observes state but does not reserve a private expiration for each reader.
`read`, `timerfd_settime`, and `close` have materially different ownership effects.

Before using timers across parallel local workers, choose explicitly between:
independent deadlines (separate timer objects), and distribution of one semantic
event (one owner plus an explicit identity-bound delivery protocol). This study
validates the former ownership boundary, not the latter delivery architecture.
Do not add a generic queue or claim model acknowledgement from a successful read.
Production integration must retain separate generation/freshness and action guards.

These are documented API semantics checked against actual processes and retained
kernel snapshots. The experiment verifies wiring and interpretation rather than
claiming an unknown OS mechanism or a same-model task benefit.

## Environment / measurement limits

Actual: Linux-6.18.44-x86_64-with-glibc2.41; CPython 3.13.5 (main, Jul 15 2026, 20:25:40) [GCC 14.2.0];
AMD EPYC 9V74 80-Core Processor. Native ABI: little-endian uint64, exactly eight bytes returned
by successful timerfd reads. CLOCK_MONOTONIC only; reported clock resolution is
software metadata, not a calibrated accuracy claim. CPU frequency/load unpinned.
No Docker/OrbStack executable or immutable image identity was available, and no
attested network-none isolation is claimed. The experiment itself makes no
network calls, installs nothing and handles no credentials/user data/GUI input.

Counts and operation order determine the result. Software scheduling and
non-simultaneous fdinfo reads limit timing interpretation, but the one-shot
state is stable between the declared operations; the future-rearm window is
checked from actual timestamp brackets. No combined timing uncertainty or
coverage factor is estimated. Two directed repetitions are finite conformance
coverage, not statistical reliability samples.

## ERROR CHECK — retained evidence

- All 20 cases complete; all 40 actor exits and both externally waited runner
  exits are 0. Both runner stderr streams are empty; no timeout occurred.
- Frozen source/plan/environment hashes: 13/13 unchanged.
- Raw-only audit: 4086 checks, errors=[]; two batches each reject all
  12 semantic corruption variants after redundant JSON frames are regenerated.
- Six offline unittest methods pass before and after formal execution.
- A copied-source modification is separately rejected as `source drift actor.py`.
- Formal invocation count: two predeclared batches, each once. Retries,
  replacements, exclusions and post-result source/gate edits: 0.
- Construction was excluded. It completed on its first ten-case invocation;
  no failed scientific row was removed or replaced.

The independent auditor is a separate implementation/process by the same author,
not an external human review. Repository-wide tests and CI were not run.
All request/response frames, complete actor stdout/stderr, external fdinfo
snapshots, commands, actual waits, frozen inputs, construction and final audits
are retained in the bundle. No historic experimental result has been rewritten.

Freeze SHA256: `e4a4338ec62037dbb1034c309ade2e9fafaa3bd770bb0bcecf62d7052fdc767a`.
Audit SHA256: `c527362686d2fc2dc11dfffb90934dabda775faac3ecdf9007937f834c8ae5b1`.

## Publication and roadmap status

Local construction, formal execution, raw audit and additive delivery are complete.
GitHub Issue/PR creation, merge, current-main checkout application, CI and remote
branch deletion were **not executed**. Current connector exposed read operations
only; plugin search returned the installed GitHub plugin without another usable
write action. Local `gh`/Docker were absent and direct GitHub DNS lookup failed.
This is a local publication constraint, not a fleet-wide block or scientific FAIL.

Issue/PR drafts accompany the evidence. A distinct successor to #4001 is justified
by multi-owner semantics, not by a wrapper incident. Preserve this first result;
publication does not authorize rerunning the formal batches. Broad roadmap and
integrated task/feedback acceptance remain uncompleted by this work.

## Read-only reproduction

From a fresh extracted study directory, with no PYTHONPATH override:

```sh
python -S -B audit_all.py . > /tmp/timerfd-ownership-audit.json
cmp AUDIT.json /tmp/timerfd-ownership-audit.json
python -S -B test_audit.py
sha256sum -c SHA256SUMS
```

The auditor imports only the separate auditor module, never actor.py or run.py.
Do not execute execute.py/run.py with consumed formal identities. A subsequent
allocation needs its own prospectively frozen schedule and declared rationale.

## Primary context

- Linux timerfd manual: https://man7.org/linux/man-pages/man2/timerfd_create.2.html
- Python os timerfd API: https://docs.python.org/3.13/library/os.html#timer-file-descriptors
- Predecessor scope: https://github.com/Unjuno/agent-interface/issues/4001
- Integration acceptance: https://github.com/Unjuno/agent-interface/issues/2789

These sources explain contracts; the local raw artifacts, not external claims,
support the measured outcomes above.
